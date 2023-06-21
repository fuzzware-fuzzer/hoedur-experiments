#!/usr/bin/env python3
import argparse
import os
import json
import shutil
import pathlib
from multiprocessing import cpu_count

# Non-standard imports
import zstandard as zst
import natsort

FUZZER_NAME = "fuzzware"
JSON_ROOT_NAME = "coverage_translation_blocks"
COVERAGE_PLOTDATA_NAME_FORMAT = "{}-run-{:02d}.json.zst"
COVERAGE_SUMMARY_NAME_FORMAT = "{}-run-{:02d}.txt"
DATA_LOOKUP_JSON_NAME = "plots.json"

def create_parser():
    parser = argparse.ArgumentParser(description="Fuzzware cross-project coverage")
    def do_help(args, leftover_args):
        parser.parse_args(['-h'])
    parser.set_defaults(func=do_help)

    parser.add_argument('--projdir_name_prefix', default="fuzzware-project-", help="Prefix for names of the fuzzware project directories to collect")
    parser.add_argument('--basedir', required=True, help="Base directory to search for Fuzzware fuzzing runs (project directories) in. For experiments, this is 'results/fuzzing-runs'. Example: hoedur-experiments/01-bug-finding-ability/results/fuzzing-runs/fuzzware")
    parser.add_argument('--outdir', required=True, help="Base directory to write results to. Note: This requires the 'coverage' directory, NOT the fuzzer-specific 'coverage/fuzzware' directory. Example: hoedur-experiments/01-bug-finding-ability/results/coverage")
    parser.add_argument('-n', '--num-workers', type=int, default=max(1, cpu_count()-1), help="The number of worker processes to spawn for emulator runs. Defaults to number of (logical) cores minus one.")

    return parser

def find_projdirs(basedir, projdir_name_prefix):
    assert(os.path.exists(basedir))

    res = []
    for dirname, subdir_names, _ in os.walk(basedir):
        if os.path.basename(dirname).startswith(projdir_name_prefix):
            res.append(dirname)

    return res

def extract_target_path_components(projdir, basedir):
    target_dir = os.path.split(projdir)[0]
    target_name = str(pathlib.Path(target_dir).relative_to(pathlib.Path(basedir)))
    proj_name = os.path.basename(projdir)

    return target_dir, target_name, proj_name

def load_json(p):
    with open(p, "r") as f:
        return json.load(f)

def save_json(path, obj, **kwargs):
    with open(path, "w") as f:
        f.write(json.dumps(obj, **kwargs))

def save_cov_summary(p, covered_bbs):
    with open(p, "w") as f:
        f.write("\n".join([f"{bb:#x}" for bb in sorted(covered_bbs)]))

def get_coverage_plot_data(projdir):
    csv_path = os.path.join(projdir, "stats", "covered_bbs_by_second_into_experiment.csv")

    plot_data = []
    covered_bbs = set()
    # There are fuzzware utils for this, but we want to avoid its dependency here
    with open(csv_path, "r") as f:
        lines = f.read().split("\n")[1:]
        for l in lines:
            if l.startswith("#") or not l:
                continue

            x_str, y_str, bbs = l.split("\t")
            plot_data.append({"x": int(x_str), "y": int(y_str)})

            bbs = bbs.rstrip("\t")
            for bb_str in bbs.split(" "):
                if not bb_str:
                    continue
                covered_bbs.add(int(bb_str, 16))

    return {
        JSON_ROOT_NAME: plot_data
    }, covered_bbs

def save_compressed_json(path, obj):
    with open(path, "wb") as f:
        f.write(zst.ZstdCompressor().compress(json.dumps(obj).encode()))

def main():
    parser = create_parser()

    args = parser.parse_args()
    basedir = args.basedir

    out_dir = args.outdir
    if not os.path.exists(out_dir):
        print(f"[ERROR] Out directory '{out_dir}' does not exist")
        exit(1)
    if not os.path.exists(basedir):
        print(f"[ERROR] Base directory '{basedir}' does not exist")
        exit(2)

    print("Collecting project dirs...")
    projdirs = sorted(find_projdirs(basedir, args.projdir_name_prefix))
    print(f"[+] Found {len(projdirs)} directories")

    projects_by_target = {}
    for p in projdirs:
        target_path, target_name, proj_name = extract_target_path_components(p, basedir)
        projects_by_target.setdefault(target_name, []).append(p)

    fuzzer_plot_data_reldir = os.path.join("charts", FUZZER_NAME)
    fuzzer_cov_summary_reldir = os.path.join("summary", FUZZER_NAME)

    os.makedirs(os.path.join(out_dir, fuzzer_plot_data_reldir), exist_ok=True)
    os.makedirs(os.path.join(out_dir, fuzzer_cov_summary_reldir), exist_ok=True)

    fuzzware_plot_data_lookup_dict = {}
    for target_name, projdirs in projects_by_target.items():
        target_data_lookup = fuzzware_plot_data_lookup_dict[target_name] = {}
        for i, projdir in enumerate(natsort.natsorted(projdirs)):
            run_no = i + 1
            target_data_relpath = os.path.join(fuzzer_plot_data_reldir, COVERAGE_PLOTDATA_NAME_FORMAT.format(target_name.replace("/", "-"), run_no))

            # Save plot data
            out_path = os.path.join(out_dir, target_data_relpath)
            plot_data, covered_bbs = get_coverage_plot_data(projdir)
            save_compressed_json(out_path, plot_data)

            # Save covered bbs summary
            cov_summary_out_path = os.path.join(out_dir, fuzzer_cov_summary_reldir, COVERAGE_SUMMARY_NAME_FORMAT.format(target_name.replace("/", "-"), run_no))
            save_cov_summary(cov_summary_out_path, covered_bbs)

            # Collect paths for lookup file
            target_data_lookup[run_no] = target_data_relpath

    # Insert fuzzware paths into lookup file
    plot_data_lookup_file_path = os.path.join(out_dir, DATA_LOOKUP_JSON_NAME)
    if os.path.exists(plot_data_lookup_file_path):
        plot_data_lookup = load_json(plot_data_lookup_file_path)
        # backup file first in case there is no backup, yet
        if not os.path.exists(plot_data_lookup_file_path+".bak"):
            shutil.copy2(plot_data_lookup_file_path, plot_data_lookup_file_path+".bak")
    else:
        plot_data_lookup = {
            "data": {},
            "plots": {}
        }

    plot_data_lookup["data"][FUZZER_NAME] = fuzzware_plot_data_lookup_dict
    save_json(plot_data_lookup_file_path, plot_data_lookup, indent=4)

if __name__ == "__main__":
    main()