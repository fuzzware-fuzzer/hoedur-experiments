#!/usr/bin/env python3

import os
import subprocess

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))

def rebuild_targets():
    # Install requirements
    print("[*] Installing python requirements to rebuild targets...")
    subprocess.check_call(["pip", "install", "-r", DIR.joinpath("04-prev-unknown-vulns", "building", "requirements.txt")])
    subprocess.check_call(DIR.joinpath("04-prev-unknown-vulns", "building", "rebuild_targets.py"))

def generate_patched_targets():
    subprocess.check_call(DIR.joinpath("02-coverage-est-data-set", "scripts", "binary-patching", "generate_patched_targets.py"))

def convert_fuzzware_target_config():
    subprocess.check_call(
        ['scripts/run_in_docker.sh', 'scripts/hoedur-convert_fuzzware_config.py'], stderr=subprocess.STDOUT)

def convert_all_hoedur_bug_detection_scripts():
    subprocess.check_call(DIR.joinpath("scripts", "fuzzware", "bug-discovery-timings", "convert_all_hoedur_bug_detection_scripts.py"))

def main():
    print("[*] Rebuilding targets...")
    rebuild_targets()
    input("[+] Rebuilding targets done. Proceed?")
    print("[*] Generating patches...")
    generate_patched_targets()
    input("[+] Generated patched targets. Proceed?")
    print("[*] Converting Fuzzware configs to Hoedur configs...")
    convert_fuzzware_target_config()
    input("[+] Converted Fuzzware configs to Hoedur configs. Proceed?")
    print("[*] Converting Hoedur bug detection scripts to Fuzzware...")
    convert_all_hoedur_bug_detection_scripts()
    print("[+] Converted Hoedur bug detection scripts to Fuzzware.")

    print("[+] All done.")

if __name__ == '__main__':
    main()
