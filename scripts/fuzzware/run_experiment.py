#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import time
import yaml

from pathlib import Path
from os.path import exists

DIR = Path(os.path.dirname(os.path.realpath(__file__)))
DIR_EXPERIMENTS_ROOT = DIR.parents[1]
DIR_TARGETS = DIR_EXPERIMENTS_ROOT.joinpath("targets", "arm")

FUZZWARE_STATISTICS_NAMES=["coverage", "crashtimings"]

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("host_run_config", help="YAML config describing the (part of the) experiment to run on this host. This is typically located in experiment-config/host-run-configs after generating them.")
    parser.add_argument("--skip-cpufreq", default=False, action="store_true", help="Tell AFL to not be worried about the CPU scaling setting.")
    parser.add_argument("--cores", default=None, type=int, help="Force the use of a specific number of maximum cores.")
    parser.add_argument("--sanity-check", default=False, action="store_true", help="Only perform sanity checks")

    return parser

def parse_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

seconds_per_time_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
def duration_string_to_seconds(s):
    # Be nice regarding spaces during parsing
    s = s.rstrip().lstrip().lower()

    try:
        num_units = int(s[:-1])
    except ValueError:
        print("[ERROR] Could not parse duration timing string: {s[:-1]}, exiting")
        exit(5)

    return num_units * seconds_per_time_unit[s[-1]]

def seconds_to_fuzzware_time_str(seconds):
    days = seconds // seconds_per_time_unit['d']
    seconds %= seconds_per_time_unit['d']
    hours = seconds // seconds_per_time_unit['h']
    seconds %= seconds_per_time_unit['h']
    minutes = seconds // seconds_per_time_unit['m']
    seconds %= seconds_per_time_unit['m']
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_fuzzware_base_target_dir(experiment_entry):
    return DIR_TARGETS.joinpath(experiment_entry['target'])

def get_results_dir(experiment_entry):
    return DIR_EXPERIMENTS_ROOT.joinpath(experiment_entry['output'], "results")

def get_fuzzware_fuzzing_run_dir(experiment_entry):
    return get_results_dir(experiment_entry).joinpath("fuzzing-runs", "fuzzware")

def get_fuzzware_output_target_dir(experiment_entry):
    return get_fuzzware_fuzzing_run_dir(experiment_entry).joinpath(experiment_entry['target'])

def fuzzware_project_name(experiment_entry):
    return f"fuzzware-project-{experiment_entry['run_id']:02d}"

def get_fuzzware_projdir(experiment_entry):
    return get_fuzzware_output_target_dir(experiment_entry).joinpath(fuzzware_project_name(experiment_entry))

def build_fuzzware_cmdline(experiment_entry):
    output_dir = get_fuzzware_output_target_dir(experiment_entry)
    cmd_args_pipeline = [
        "fuzzware", "pipeline",
        "-n", str(experiment_entry["cores_per_run"]),
        "--run-for", seconds_to_fuzzware_time_str(experiment_entry['duration']),
        "-p", fuzzware_project_name(experiment_entry),
        "--runtime-config-name", "config_fuzzware.yml",
        output_dir
    ]
    cmd_args_genstats = [
        "fuzzware", "genstats",
        "-p", get_fuzzware_projdir(experiment_entry)
    ] + FUZZWARE_STATISTICS_NAMES
    return cmd_args_pipeline, cmd_args_genstats

def next_experiment_entry(available_cores, experiment_entries):
    for i in range(len(experiment_entries)):
        if experiment_entries[i]["cores_per_run"] <= available_cores:
            return i

    return None

def sanity_check():
    p = subprocess.Popen(["fuzzware", "checkenv"], stdout=subprocess.PIPE)
    stdout_output, _ = p.communicate()
    if p.returncode != 0:
        return False, stdout_output.decode()
    else:
        return True, None

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    config_path = args.host_run_config
    skip_cpufreq = args.skip_cpufreq
    forced_num_cores = args.cores

    if skip_cpufreq:
        os.environ['AFL_SKIP_CPUFREQ'] = "1"

    if not exists(config_path):
        print(f"[FUZZWARE] [ERROR] Could not find config at {config_path}, exiting...")
        exit(1)

    config = parse_yaml(config_path)

    if "cores" not in config:
        print(f"[FUZZWARE] [ERROR] No 'cores' entry found. The config seems to be mis-formatted. Exiting...")
        exit(2)
    cores_cfg = config["cores"]
    if type(cores_cfg) != dict:
        print(f"[FUZZWARE] [ERROR] 'cores' is no dictionary. The config seems to be mis-formatted. Exiting...")
        exit(3)

    max_cores = forced_num_cores
    if max_cores is None:
        max_cores = cores_cfg.get("fuzzware", None)

    # Extract all runs that we need to perform
    experiment_entries = [run for run in config.get("runs", []) if run.get("fuzzer", "").lower() == "fuzzware"]

    # Pre-process config entries
    for entry in experiment_entries:
        entry['duration'] = duration_string_to_seconds(entry['duration'])

        entry.setdefault("cores_per_run", 1)

        target_output_dir = get_fuzzware_output_target_dir(entry)
        if not target_output_dir.exists():
            target_base_binary_dir = get_fuzzware_base_target_dir(entry)
            print(f"[FUZZWARE] [SETUP] Copying binaries from {target_base_binary_dir} to {target_output_dir}")
            shutil.copytree(target_base_binary_dir, target_output_dir)

    # Sort to put the runs that require the most cores first
    experiment_entries.sort(key=lambda e: e['duration'], reverse=True)

    if (not max_cores) and experiment_entries:
        print(f"[FUZZWARE] [ERROR] Found experiments for fuzzware to run, but cfg['cores']['fuzzware'] contains a zero value or no value at all. Example experiment entry: {experiment_entries[0]}")
        exit(4)

    check_passed, sanity_check_output = sanity_check()
    if not check_passed:
        print(f"[FUZZWARE] [ERROR] Sanity check failed. Output: {sanity_check_output}")
        exit(5)

    if args.sanity_check:
        exit(0)

    # Execute runs
    available_cores = max_cores
    running_instances = []

    print(f"[FUZZWARE] [RUN] Found {len(experiment_entries)} experiment entries to run")

    try:
        while experiment_entries or running_instances:
            was_active = False
            for inst_no, inst in enumerate(running_instances):
                proc, start_time, exp_entry, remaining_follow_up_cmds = inst
                # Process still running?
                if proc.poll() is None:
                    continue

                was_active = True
                # Process has finished. Let's see about its status

                error_message = ""
                # Did process error?
                if proc.returncode != 0:
                    error_message += "Process returned a non-zero return code"

                # Did fuzzing process end prematurely?
                proc_runtime = time.time() - start_time
                if remaining_follow_up_cmds and (proc_runtime < (exp_entry['duration'] / 10)):
                    error_message += "Process ended abruptly"

                if error_message:
                    projdir_relpath = get_fuzzware_projdir(exp_entry).relative_to(DIR_EXPERIMENTS_ROOT)
                    print(f"[FUZZWARE] [ERROR] Failed to execute {exp_entry['target']} run {exp_entry['run_id']:02d}. Reason: {error_message}")
                    print(f"[FUZZWARE] [ERROR] Command-line (to be run in Fuzzware eval docker container): '{' '.join(map(str, proc.args))}'")
                    print(f"[FUZZWARE] [ERROR] Please refer to the logs in {projdir_relpath} to figure out the issue")
                    print(f"[FUZZWARE] [ERROR] Killing all remaining instances and stopping the experiment")
                    # Kill all processes
                    for e in running_instances:
                        e[0].kill()
                    exit(6)

                # Run went well

                # Do we still need to run statistics generation?
                if remaining_follow_up_cmds:
                    cmd = remaining_follow_up_cmds.pop(0)
                    print(f"[FUZZWARE] [RUN] [*] Starting metric collection for target {exp_entry['target']} run {exp_entry['run_id']:02d}")
                    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    inst[0] = proc
                else:
                    # all done here, remove and release cores
                    running_instances.pop(inst_no)
                    print(f"[FUZZWARE] [RUN] [+] Completed target {exp_entry['target']} run {exp_entry['run_id']:02d}")
                    available_cores += exp_entry['cores_per_run']
                    break

            # Schedule new processes if we have space
            while available_cores > 0:
                next_exp_ind = next_experiment_entry(available_cores, experiment_entries)

                if next_exp_ind is None:
                    break

                was_active = True

                exp_entry = experiment_entries.pop(next_exp_ind)
                available_cores -= exp_entry["cores_per_run"]

                cmd_args_pipeline, cmd_args_genstats = build_fuzzware_cmdline(exp_entry)

                start_time = time.time()
                proc = subprocess.Popen(cmd_args_pipeline, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                remaining_follow_up_cmds = [ cmd_args_genstats ]

                print(f"[FUZZWARE] [RUN] [*] Starting target {exp_entry['target']} run {exp_entry['run_id']:02d}")
                running_instances.append([proc, start_time, exp_entry, remaining_follow_up_cmds])

                # Give the instance time to start and let AFL figure out its core affinity
                time.sleep(5)

            if not was_active:
                time.sleep(30)
    except KeyboardInterrupt:
        print("Got keyboard interrupt. Stopping...")
        exit(7)

    print(f"[FUZZWARE] [RUN] all done")
    exit(0)
