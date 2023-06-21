#!/usr/bin/env python3
""" This script looks for fuzzware projects starting from a
base directory and scans them for different fuzzing performance
statistics.

Currently, the following statistics are collected:
- Number of executions per second (placed in results/statistics/executions/fuzzware.txt)
"""

import argparse
import os
import subprocess

from pathlib import Path

FUZZER_NAME = "fuzzware"
JSON_ROOT_NAME = "executions_per_second"
EXECS_METRIC_DIR_NAME = "executions"
PLOT_DATA_NAME_FORMAT = "{}-run-{:02d}-core-{:02d}.json.zst"
COVERAGE_SUMMARY_NAME_FORMAT = "{}-run-{:02d}.txt"
DATA_LOOKUP_JSON_NAME = "plots.json"
FILENAME_EXECS_SUMMARY = f"{FUZZER_NAME}.txt"
DEFAULT_OUTDIR_RELPATH = os.path.join("..", "..", "statistics")

# Fuzzware imports
try:
    from fuzzware_pipeline.util import eval_utils
    import fuzzware_pipeline.naming_conventions as nc
except ModuleNotFoundError:
    print("[ERROR] Could not import Fuzzware modules. Please run in a Fuzzware virtualenv or Fuzzware docker container.")
    exit(1)

# Non-standard imports
try:
    import natsort
except ModuleNotFoundError:
    print("[ERROR] Could not import the natsort module. Please install this module in the Fuzzware execution environment you are using.")
    exit(1)

def find_projdirs(basedir, projdir_name_prefix):
    assert(os.path.exists(basedir))

    res = []
    for dirname, subdir_names, _ in os.walk(basedir):
        if os.path.basename(dirname).startswith(projdir_name_prefix):
            res.append(dirname)

    return res

def load_json(p):
    with open(p, "r") as f:
        return json.load(f)

def save_json(path, obj, **kwargs):
    with open(path, "w") as f:
        f.write(json.dumps(obj, **kwargs))

def extract_target_path_components(projdir, basedir):
    target_dir = os.path.split(projdir)[0]
    target_name = str(Path(target_dir).relative_to(Path(basedir)))
    proj_name = os.path.basename(projdir)

    return target_dir, target_name, proj_name

def sanity_checks_valid():
    try:
        subprocess.check_output(["fuzzware", "-h"])
    except subprocess.CalledProcessError:
        return False
    return True

def collect_execs_per_sec(projdir):
    start_time = eval_utils.find_start_time(projdir)
    run_time = eval_utils.find_run_time(projdir)
    throughputs_per_core = []
    total_execs_done = 0
    num_fuzzers = 0
    for main_dir_ind, main_dir in enumerate(nc.main_dirs_for_proj(projdir)):
        fuzzer_dirs = nc.fuzzer_dirs_for_main_dir(main_dir)
        if main_dir_ind == 0:
            throughputs_per_core.extend(len(fuzzer_dirs) * [[{'x': 0, 'y': 0}]])

        num_fuzzers = len(fuzzer_dirs)
        for fuzzer_no, fuzzer_dir in enumerate(fuzzer_dirs):
            try:
                fuzzer_stats = eval_utils.parse_afl_fuzzer_stats(os.path.join(fuzzer_dir, "fuzzer_stats"))
                total_execs_done += int(fuzzer_stats["execs_done"])
            except FileNotFoundError:
                pass

            print(fuzzer_no, fuzzer_dir)
            throughputs = throughputs_per_core[fuzzer_no]
            for entry in eval_utils.parse_afl_plot_data(os.path.join(fuzzer_dir, "plot_data")):
                # unix_time, cycles_done, cur_path, paths_total, pending_total, pending_favs, map_size, unique_crashes, unique_hangs, max_depth, execs_per_sec
                unix_time = entry[0]
                execs_per_sec = entry[-1]
                throughputs.append({"x": unix_time-start_time, "y": execs_per_sec})

    return (run_time * num_fuzzers, total_execs_done), throughputs_per_core

def main():
    parser = argparse.ArgumentParser(description="Fuzzware cross-project statistics gathering")
    def do_help(args, leftover_args):
        parser.parse_args(['-h'])
    parser.set_defaults(func=do_help)

    parser.add_argument('--basedir', required=True, help="Base directory to search for Fuzzware fuzzing runs (project directories) in. For experiments, this is 'results/fuzzing-runs'. Example: hoedur-experiments/01-bug-finding-ability/results/fuzzing-runs/fuzzware")
    parser.add_argument('--outdir', default=None, help=f"Base directory to write results to. Defaults to <basedir>/{DEFAULT_OUTDIR_RELPATH}. Example: hoedur-experiments/01-bug-finding-ability/results/statistics/Fuzzware")
    parser.add_argument('--projdir_name_prefix', default="fuzzware-project-", help="Prefix for names of the fuzzware project directories to collect")

    args = parser.parse_args()
    basedir = args.basedir

    if not os.path.exists(basedir):
        print(f"[ERROR] Base directory '{basedir}' does not exist")
        exit(2)

    if not sanity_checks_valid():
        print("[ERROR] Cannot run fuzzware. Are we inside a docker container or virtualenv? Try 'fuzzware -h' to troubleshoot the issue")
        exit(3)

    print("Collecting project dirs...")
    projdirs = find_projdirs(basedir, args.projdir_name_prefix)
    print(f"[+] Found {len(projdirs)} directories")
    print(f"Project directories: {projdirs}")

    out_dir = args.outdir
    if out_dir is None:
        out_dir = os.path.join(basedir, DEFAULT_OUTDIR_RELPATH)

    if not os.path.exists(out_dir):
        print(f"[*]] Out directory '{out_dir}' does not exist, yet - creating it")
        os.makedirs(out_dir)

    # 1. Collect execs per second
    execs_per_seconds_per_target = {}
    total_execs_per_target = {}
    total_runtime_per_target = {}

    print("Collecting execs/s...")
    # We need to collect the executions per second for each main directory and each CPU core (main*/fuzzers/fuzzer{1,2,3,4,...})
    for projdir in projdirs:
        print(f"Processing {projdir}...")
        target_dir, target_name, proj_name = extract_target_path_components(projdir, basedir)
        (runtime, execs_done), execs_plot_data = collect_execs_per_sec(projdir)
        execs_per_seconds_per_target.setdefault(target_name, {})[proj_name] = execs_plot_data
        total_execs_per_target.setdefault(target_name, 0)
        total_runtime_per_target.setdefault(target_name, 0)

        total_runtime_per_target[target_name] += runtime
        total_execs_per_target[target_name] += execs_done

    os.makedirs(os.path.join(out_dir, EXECS_METRIC_DIR_NAME), exist_ok=True)

    projects_by_target = {}
    for p in projdirs:
        target_path, target_name, proj_name = extract_target_path_components(p, basedir)
        projects_by_target.setdefault(target_name, []).append(p)

    execs_per_sec_summary = ""
    max_name_len = max([len(target_name) for target_name in total_runtime_per_target.keys()])
    for i, target_name in enumerate(natsort.natsorted(total_runtime_per_target.keys())):
        runtime, execs_done = total_runtime_per_target[target_name], total_execs_per_target[target_name]

        if i != 0:
            execs_per_sec_summary += "\n"
        execs_per_sec_summary += f"{target_name.ljust(max_name_len+1)}{round(execs_done/runtime, 2)}"

    with open(os.path.join(out_dir, EXECS_METRIC_DIR_NAME, FILENAME_EXECS_SUMMARY), "w") as f:
        f.write(execs_per_sec_summary)
    print(execs_per_sec_summary)

if __name__ == "__main__":
    main()