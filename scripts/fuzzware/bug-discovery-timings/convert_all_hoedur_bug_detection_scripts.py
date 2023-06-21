#!/usr/bin/env python3
"""
Given
"""

import argparse
import filecmp
import os
import subprocess

from os.path import exists, join
from pathlib import Path

# colors
GREEN = "\033[92m"
RED = "\033[91m"
ENDC = "\033[0m"

DIR = Path(os.path.dirname(os.path.realpath(__file__)))
CONV_SCRIPT_FILENAME = "convert_hoedur_bug_detection_script.py"

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets-basedir", default=DIR.parents[2].joinpath("targets", "arm", "Fuzzware"), help="Directory containing the target configurations to start searching in.")
    parser.add_argument("--hoedur-script-name", default="hook-bugs.rn", help="Name of Hoedur bug detection hook scripts to be converted.")
    parser.add_argument("--out-script-name", default="hook_bugs_fuzzware_regen.py", help="Output file name of Fuzzware bug detection hooks.")
    parser.add_argument("--compare-script-name", default="hook_bugs_fuzzware.py", help="Reference output file name of Fuzzware bug detection hooks to compare to.")
    return parser

def find_dirs_containing_filename(basedir, filename):
    res = []

    for dirname, subdir_names, file_names in os.walk(basedir):
        if filename in file_names:
            res.append(dirname)

    return res

def main():
    parser = create_parser()
    args = parser.parse_args()

    basedir = Path(args.targets_basedir)
    hoedur_scriptname = args.hoedur_script_name
    fuzzware_scriptname = args.out_script_name
    ref_fuzzware_scriptname = args.compare_script_name

    assert(exists(basedir))

    target_dirs = find_dirs_containing_filename(basedir, hoedur_scriptname)
    for d in target_dirs:
        target_relpath = Path(d).relative_to(basedir)
        hoedur_script = join(d, hoedur_scriptname)
        fuzzware_script = join(d, fuzzware_scriptname)
        fuzzware_reference_script = join(d, ref_fuzzware_scriptname)
        assert(exists(hoedur_script))

        print(f"Converting script: {join(target_relpath, hoedur_scriptname)}")
        subprocess.check_output([DIR.joinpath(CONV_SCRIPT_FILENAME), "--force", hoedur_script, fuzzware_script])

        if not exists(fuzzware_script):
            print(RED, end="")
            print(f"Converting to {join(target_relpath, fuzzware_scriptname):15} failed (no config produced)")
            print(ENDC, end="")
        elif exists(fuzzware_reference_script):
            match = filecmp.cmp(fuzzware_script, fuzzware_reference_script, shallow=False)

            if match:
                print(GREEN, end="")
            else:
                print(RED, end="")
            print(f"Converted script {join(target_relpath, fuzzware_scriptname):15} matching configs {match}")
            print(ENDC, end="")

if __name__ == '__main__':
    main()
