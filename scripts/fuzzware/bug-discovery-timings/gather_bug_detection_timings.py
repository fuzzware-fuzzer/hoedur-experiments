#!/usr/bin/env python3
""" This script looks for fuzzware projects with bug detection hooks
starting from a base directory and scans them for the timing when
different bugs were detected.

The bug detection timings are gathered by running all crashing
inputs under bug detection hooks. These detection hooks are designed
to indicate whether a given input triggers a known bug. The bug
detection hooks can be found in the target directory under file name
hook_bugs_fuzzware.py.
"""

import argparse
import os
import subprocess
import yaml
import copy
import hashlib
import re
import time
from multiprocessing import Pool, cpu_count

from pathlib import Path

try:
    from fuzzware_pipeline.util.eval_utils import parse_input_file_timings
    from fuzzware_pipeline.util.config import save_config
    import fuzzware_pipeline.naming_conventions as nc
except ModuleNotFoundError:
    print("[ERROR] Could not import Fuzzware modules. Please run in a Fuzzware virtualenv or Fuzzware docker container.")
    exit(1)

HOOK_APPLICATION_ENV = copy.deepcopy(os.environ)
CONFIG_YAML_BASE_FILE_NAME = "config_fuzzware.yml"

DEFAULT_OUTDIR_RELPATH = os.path.join("..", "..", "bug-discovery-timings", "fuzzware")

# Default name of function
BUG_DETECTION_HOOK_FUNC_DEFAULT_NAME = "detect_bug"
BUG_DETECTION_HOOK_FILE_NAME = "hook_bugs_fuzzware.py"
# Name of file to use while generating config which is placed in the respective mainXXX/ directories
DETECTION_HOOK_CONFIG_NAME = "config_detection_hook.yml"

CACHED_BUG_DETECTION_HOOK_RES_FILE_NAME = "bug_detection_hook_results.yml"
REPORT_TIME_CACHED_RESULTS_INTERVAL = 1000
SAVE_CACHED_RESULTS_INTERVAL = 10 * REPORT_TIME_CACHED_RESULTS_INTERVAL

BUG_COMBINATION_YAML_NAME_FORMAT = "bug-combinations-run-{:02d}.yml"

BUG_DETECTION_REGEX = re.compile('Heureka! ([A-Za-z_\\-0-9]*)')

def find_projdirs(basedir, projdir_name_prefix):
    assert(os.path.exists(basedir))

    res = []
    for dirname, subdir_names, _ in os.walk(basedir):
        if os.path.basename(dirname).startswith(projdir_name_prefix):
            res.append(dirname)

    return res

def summarize_detection_timings(cached_bug_detection_results):
    """ Collect the minimum timings of bug detection for
    - Each bug individually
    - Each combination of detected bugs
    """
    timings_per_target = {}

    for target_name, target_map in cached_bug_detection_results.items():
        timings_per_target[target_name] = {}
        for detection_script_sha1, run_map in target_map.items():
            timings_per_target[target_name][detection_script_sha1] = {}
            
            for run_name, crashing_input_map in run_map.items():
                best_timings_per_bug_combination = timings_per_target[target_name][detection_script_sha1][run_name] = {}
                for input_path, detection_entry in crashing_input_map.items():
                    triggered_bugs = "|".join(sorted(detection_entry["BugCombination"]))
                    if not triggered_bugs:
                        triggered_bugs = "NO_BUG_DETECTED"
                    crash_time = detection_entry["time"]
                    current_shortest_time = best_timings_per_bug_combination.setdefault(triggered_bugs, crash_time)
                    if crash_time < current_shortest_time:
                        best_timings_per_bug_combination[triggered_bugs] = crash_time

    return timings_per_target

def extract_bug_detection_hook_cfg(bug_detection_py_script_path):
    """
    Given a bug detection hook script, generate a fuzzware config
    that uses the detection hooks that are specified within the bug
    detection python script.

    Fuzzware bug detection hooks by convention at the start of the
    file contain a list of comment lines that specify hook functions
    as well as their locations with the following format:

    ```
    ## Internal comment via two pound signs
    # <hook_location> [<hook_function_name>]
    ```

    Examples:
    ```
    ## Address literal and explicit function name
    # 0xdeadbeef my_fn
    ## Symbol and explicit function name
    # main my_fn
    ## Symbol with offset and explicit function name
    # main+0x12 my_fn
    ## Address literal without function name defaults to 'detect_bug'
    # 0xdeadbeef
    ```
    """

    if not os.path.exists(bug_detection_py_script_path):
        return None, None

    # First parse hooking addresses and hook function names from file header lines
    hook_addrs = set()
    with open(bug_detection_py_script_path, "rb") as f:
        contents = f.read()
        hashsum = hashlib.sha1(contents).hexdigest()
        lines = contents.split(b"\n")
        for l in lines:
            print(f"Looking at line: {l}")
            if (not l) or l[:1] != b"#" or l.startswith(b"###"):
                # Stop parsing on first empty/non-comment line
                print("Breaking on empty / non-comment line")
                break
            elif l.startswith(b"##"):
                print("Line is internal comment")
                # Internal comment via ##
                continue

            l = l[1:]
            if not l:
                print("Skipping empty comment")
                # Skip empty comment lines
                continue
            # Strip leading blanks
            while l[:1] == b" ":
                print(f"Stripping blank space from line {l}")
                l = l[1:]
            # Also normalize any blanks around symbol offset "+" signs
            while b" +" in l:
                l = l.replace(b" +", b"+")
            while b"+ " in l:
                l = l.replace(b"+ ", b"+")

            print(f"Line after normalization: {l}")

            # Formats:
            # <address>
            # <address> <hook_name>
            tokens = l.split(b" ")
            assert(1 <= len(tokens) <= 2)
            hook_addr = tokens[0]

            try:
                hook_addr = int(hook_addr, 16)
            except ValueError:
                hook_addr = hook_addr.decode()

            # If a second token is given, we got the hook name
            if len(tokens) == 2:
                hook_name = tokens[1].rstrip().decode()
            else:
                hook_name = BUG_DETECTION_HOOK_FUNC_DEFAULT_NAME

            hook_addrs.add((hook_addr, hook_name))

    detection_handler_cfg = {}
    for hook_addr, hook_name in hook_addrs:
        detection_handler_cfg[f"detection_hook_{hook_addr}"] = {
            "addr": hook_addr,
            "do_return": False,
            "handler": BUG_DETECTION_HOOK_FILE_NAME.split(".")[0] + "." + hook_name
        }

    return {
        "handlers": detection_handler_cfg,
        "include": [
            os.path.join("./"+nc.SESS_FILENAME_CONFIG)
        ]
    }, hashsum

def save_yaml(path, results):
    with open(path, "w") as f:
        f.write(yaml.dump(results))

def load_yaml(path):
    if not os.path.exists(path):
        return {}

    with open(path, 'rb') as infile:
        results = yaml.load(infile, Loader=yaml.FullLoader)

    if not results:
        results = {}

    return results

def dump_hoedur_compatible_results(basedir, out_dir, cached_bug_detection_results):

    for target_path, script_hashsum_to_result in cached_bug_detection_results.items():
        # Get the results for the current detection script
        detection_hook_path = os.path.join(basedir, target_path, BUG_DETECTION_HOOK_FILE_NAME)
        try:
            with open(detection_hook_path, "rb") as f:
                contents = f.read()
                hashsum = hashlib.sha1(contents).hexdigest()
        except FileNotFoundError:
            print(f"[ERROR] Could not find current bug detection hooks at {detection_hook_path}")
            exit(6)

        if hashsum not in script_hashsum_to_result:
            print(f"[ERROR] could not find detection results for detection hooks in {detection_hook_path}")
            exit(6)

        projdir_results = script_hashsum_to_result[hashsum]
        # Number runs by alphabetical order
        sorted_proj_names = sorted(projdir_results.keys())
        for fuzz_run_no, proj_name in enumerate(sorted_proj_names):
            # We collect all inputs/bug combinations per fuzzing run and to store it at
            # <outdir>/<Path/to/target>/bug-combinations-run-<run_no>.yml
            # e.g.: Fuzzware/zephyr-os/CVE-2020-10066/bug-combinations-run-01.yml
            # Location in experiments: hoedur-experiments/01-bug-finding-ability/results/bug-discovery-timings/<fuzzer_name>/Fuzzware/zephyr-os/CVE-2020-10066/bug-combinations-run-01.yml
            run_results_list = []
            # Count one-based, not zero-based
            fuzz_run_no += 1

            bugs_by_input_path = projdir_results[proj_name]
            for input_path, result_map in bugs_by_input_path.items():
                # Build a rust serde-compabible representation
                bug_combination = result_map["BugCombination"]
                time = result_map["time"]
                fuzzware_project_path = os.path.join(target_path, proj_name)
                entry = [
                    {'BugCombination': bug_combination},
                    {
                        'time': time,
                        'source': {
                            # We are taking liberties in the format here and add an actual path, not an id integer
                            'input': input_path,
                            'report': fuzzware_project_path
                        }
                    }
                ]
                run_results_list.append(entry)

            yaml_result_name = BUG_COMBINATION_YAML_NAME_FORMAT.format(fuzz_run_no)
            # We place the result file in a directory structure equivalent to the location of the project directory
            output_yaml_dir = os.path.join(out_dir, target_path)
            output_yaml_path = os.path.join(output_yaml_dir, yaml_result_name)
            if not os.path.exists(output_yaml_dir):
                os.makedirs(output_yaml_dir)

            print(f"Saving results to {output_yaml_path}")
            save_yaml(output_yaml_path, run_results_list)


def workload_bugs_triggered_by_input(crash_path, bug_detection_hook_cfg):
    main_no, fuzzer_no = nc.main_and_fuzzer_number(crash_path)
    proj_dir_path = nc.project_base(crash_path)
    target_dir_path = os.path.split(proj_dir_path)[0]
    main_dir_path = nc.main_dirs_for_proj(proj_dir_path)[main_no-1]
    bug_detection_config_path = os.path.join(main_dir_path, DETECTION_HOOK_CONFIG_NAME)

    if not os.path.exists(bug_detection_config_path):
        save_config(bug_detection_hook_cfg, bug_detection_config_path)

    # Now execute crashing input with bug detection hooks enabled
    try:
        # Set pythonpath env var to parent of the project directory so that bug detection hooks are accessible
        HOOK_APPLICATION_ENV["PYTHONPATH"] = target_dir_path
        output = subprocess.check_output(["fuzzware", "emu", "-c", bug_detection_config_path, crash_path], env=HOOK_APPLICATION_ENV)

        output = output.decode()
        # print(output, flush=True)
        # Collect all detected bugs via the stdout output
        return list(set(BUG_DETECTION_REGEX.findall(output)))
    except subprocess.CalledProcessError:
        print(f"[WARNING] Process errored for crashing input {crash_path}")
        return None

def workload_gather_crash_timings(projdir):
    try:
        subprocess.check_call(["fuzzware", "genstats", "-p",  projdir, "crashtimings"])
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Generating crash timings failed, skipping project directory")
        return False

    return True

def extract_target_path_components(projdir, basedir):
    target_dir = os.path.split(projdir)[0]
    target_name = str(Path(target_dir).relative_to(Path(basedir)))
    proj_name = os.path.basename(projdir)

    return target_dir, target_name, proj_name

def gen_missing_crash_timings(projdirs, worker_pool):
    crash_timing_workloads = []

    for projdir in projdirs:
        crash_timings_path = nc.crash_creation_timings_path(projdir)
        if not os.path.exists(crash_timings_path):
            crash_timing_workloads.append(projdir)

    failed_projdirs = []
    if crash_timing_workloads:
        print(f"[Crash Timings] Generating crash timings file for {len(crash_timing_workloads)} projects")
        crash_timing_worker_results = {projdir: worker_pool.apply_async(workload_gather_crash_timings, (projdir, )) for projdir in crash_timing_workloads}

        for projdir, async_res in crash_timing_worker_results.items():
            res = async_res.get()

            if res is not True:
                print(f"[WARNING] Ignoring project dir as crash timings could not be retrieved: '{projdir}'")
                failed_projdirs.append(projdir)
    else:
        print("[Crash Timings] [+] All crash timings already generated!")

    return failed_projdirs

def collect_bug_detection_workloads(basedir, cached_bug_detection_results, projdirs):
    """ Pre-collect all jobs that need to be run for bug detection """

    workloads = []
    bug_detect_hook_cfg_per_target = {}

    for projdir in projdirs:
        target_dir, target_name, proj_name = extract_target_path_components(projdir, basedir)

        if target_name not in bug_detect_hook_cfg_per_target:
            """ New target encountered. Generate config
            """
            detection_hook_script_path = os.path.join(target_dir, BUG_DETECTION_HOOK_FILE_NAME)

            bug_detect_hook_cfg_per_target[target_name] = extract_bug_detection_hook_cfg(detection_hook_script_path)
            if bug_detect_hook_cfg_per_target[target_name][0]:
                print(f"[+] Generated bug detection config for {target_name}: {bug_detect_hook_cfg_per_target[target_name]}")
            else:
                print(f"[*] No bug detection config found for {target_name}")

            for main_dir in nc.main_dirs_for_proj(projdir):
                try:
                    os.remove(os.path.join(main_dir, DETECTION_HOOK_CONFIG_NAME))
                except:
                    pass

        bug_detect_hook_cfg, bug_detect_hook_sha1 = bug_detect_hook_cfg_per_target[target_name]

        cached_bugs_for_target = cached_bug_detection_results.setdefault(
            target_name, {}).setdefault(
                bug_detect_hook_sha1, {}).setdefault(
                    proj_name, {})

        crash_timings_path = nc.crash_creation_timings_path(projdir)
        seconds_and_crash_path = parse_input_file_timings(crash_timings_path)

        # Preliminary check #1: Any crashes for target?
        if not seconds_and_crash_path:
            continue

        # Preliminary check #2: Bug detection config for target?
        if not bug_detect_hook_cfg:
            continue

        # This is where we have crashing inputs and a bug detection script
        for seconds_to_crash, crash_path in seconds_and_crash_path:
            full_crash_path = os.path.join(projdir, crash_path)

            if crash_path in cached_bugs_for_target:
                print(f"Using cached bug results for crashing input: {crash_path}")
                pass
            else:
                print(f"Adding bug detection job for crashing input: {crash_path}")
                lookup_key = (cached_bugs_for_target, crash_path, seconds_to_crash)
                workload_args = (full_crash_path, bug_detect_hook_cfg)
                workloads.append((lookup_key, workload_args))

    return workloads

def run_bug_detection_workloads(cached_bug_detection_results, cached_bug_detection_results_path, worker_pool, detection_run_workloads):
    """ Run the workloads previously collected
    Also regularly give a progress update
    """
    if not detection_run_workloads:
        print("[Bug Detection Timing Collection] [+] All bug detection results already collected / cached!")
        return True

    print(f"[Bug Detection Timing Collection] Generating bug detection for {len(detection_run_workloads)} crashing inputs")
    num_workloads = len(detection_run_workloads)
    crash_timing_worker_results = [(lookup_key, (full_crash_path, bug_detect_hook_cfg), worker_pool.apply_async(workload_bugs_triggered_by_input, (full_crash_path, bug_detect_hook_cfg))) for (lookup_key, (full_crash_path, bug_detect_hook_cfg)) in detection_run_workloads]

    num_processed = 0
    time_start = time.time()
    for (cached_bugs_for_target, crash_path, seconds_to_crash), (full_crash_path, bug_detect_hook_cfg), async_res in crash_timing_worker_results:
        detected_bug_names = async_res.get()

        if detected_bug_names is None:
            print(f"[WARNING] Running crashing input resulted in an error while running Fuzzware: '{crash_path}'")
            detected_bug_names = ["_ERROR WHILE EXECUTING_"]
            return False

        cached_bugs_for_target[crash_path] = {
            "BugCombination": detected_bug_names,
            "time": seconds_to_crash
        }
        num_processed += 1

        print(f"Processed crashing input: {full_crash_path} with config {bug_detect_hook_cfg}.\nResult: {detected_bug_names}")

        if num_processed % REPORT_TIME_CACHED_RESULTS_INTERVAL == 0:
            time_spent = time.time()-time_start
            avg_time = time_spent / num_processed
            est_remaining = avg_time * (num_workloads - num_processed)
            print(f"Processed {num_processed:d}/{num_workloads:d} in {time_spent}. Estimated time remaining: {round(est_remaining)}...")
            if num_processed % SAVE_CACHED_RESULTS_INTERVAL == 0:
                save_yaml(cached_bug_detection_results_path, cached_bug_detection_results)

    return True

def sanity_checks_valid():
    try:
        subprocess.check_output(["fuzzware", "-h"])
    except subprocess.CalledProcessError:
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Fuzzware cross-project crash timing gathering")
    def do_help(args, leftover_args):
        parser.parse_args(['-h'])
    parser.set_defaults(func=do_help)

    parser.add_argument('--basedir', required=True, help="Base directory to search for Fuzzware fuzzing runs (project directories) in. For experiments, this is 'results/fuzzing-runs'. Example: hoedur-experiments/01-bug-finding-ability/results/fuzzing-runs/fuzzware")
    parser.add_argument('--outdir', default=None, help=f"Base directory to write results to. Defaults to <basedir>/{DEFAULT_OUTDIR_RELPATH}. Example: hoedur-experiments/01-bug-finding-ability/results/bug-discovery-timings/fuzzware")
    parser.add_argument('--projdir_name_prefix', default="fuzzware-project-", help="The directory name prefixes of the fuzzware projects to collect")
    parser.add_argument('-n', '--num-workers', type=int, default=max(1, cpu_count()-1), help="The number of worker processes to spawn for emulator runs. Defaults to number of (logical) cores minus one.")

    args = parser.parse_args()
    basedir = args.basedir

    if not os.path.exists(basedir):
        print(f"[ERROR] Base directory '{basedir}' does not exist")
        exit(2)
    
    if not sanity_checks_valid():
        print("[ERROR] Cannot run fuzzware. Are we inside a docker container or virtualenv? Try 'fuzzware -h' to troubleshoot the issue")
        exit(3)

    print("[*] Collecting project dirs...")
    projdirs = sorted(find_projdirs(basedir, args.projdir_name_prefix))
    print(f"[+] Found {len(projdirs)} directories")

    print("[*] Checking bug detection hook presence...")
    projdirs = [ projdir for projdir in projdirs if \
        Path(projdir).parent.joinpath(BUG_DETECTION_HOOK_FILE_NAME).exists()
    ]
    if projdirs:
        print(f"[+] Got {len(projdirs)} directories with bug detection hooks.")
    else:
        print(f"[*] No projects contain bug detection hooks. Nothing to be done here.")
        exit(0)

    out_dir = args.outdir
    if out_dir is None:
        out_dir = os.path.join(basedir, DEFAULT_OUTDIR_RELPATH)

    if not os.path.exists(out_dir):
        print(f"[*]] Out directory '{out_dir}' does not exist, yet - creating it")
        os.makedirs(out_dir)

    worker_pool = Pool(args.num_workers)

    # First, prepare projects by generating crash timings
    failed_crash_timing_gen_projects = gen_missing_crash_timings(projdirs, worker_pool)
    if failed_crash_timing_gen_projects:
        print(f"[WARNING] Got fails for crash timing generation. Number of failed projects: {len(failed_crash_timing_gen_projects)}")
        for projdir in failed_crash_timing_gen_projects:
            projdirs.remove(projdir)

    print("Loading bug detection run results...")
    cached_bug_detection_results_path = os.path.join(out_dir, CACHED_BUG_DETECTION_HOOK_RES_FILE_NAME)
    cached_bug_hook_results = load_yaml(cached_bug_detection_results_path)
    print("[+] Loaded results")

    # Second, collect all crashing inputs for which we need to run the bug detection
    detection_run_workloads = collect_bug_detection_workloads(basedir, cached_bug_hook_results, projdirs)

    print(f"Number of required bug detection runs: {len(detection_run_workloads)}")

    try:
        bug_detection_success = run_bug_detection_workloads(cached_bug_hook_results, cached_bug_detection_results_path, worker_pool, detection_run_workloads)
    finally:
        print("Saving cached bug hook results...")
        save_yaml(cached_bug_detection_results_path, cached_bug_hook_results)

    if not bug_detection_success:
        print("[ERROR] There have been errors while running inputs under detection hooks")
        exit(4)

    detection_timing_summary = summarize_detection_timings(cached_bug_hook_results)
    save_yaml(os.path.join(out_dir, "detection_timings.yml"), detection_timing_summary)

    dump_hoedur_compatible_results(basedir, out_dir, cached_bug_hook_results)

if __name__ == "__main__":
    main()