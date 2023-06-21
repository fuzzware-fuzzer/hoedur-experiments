#!/usr/bin/env python3

import os
import subprocess
from subprocess import PIPE

from glob import glob
from pathlib import Path

from generate_host_run_config import load_available_hosts

DIR = Path(os.path.dirname(os.path.realpath(__file__)))

def check_rsync():
    subprocess.check_output(["rsync", "-h"])

def check_host(hostname):
    proc = subprocess.Popen(["ssh", hostname, "ls", "hoedur-experiments"], stdout=PIPE, stderr=PIPE)
    stdout_output, stderr_output = proc.communicate()
    return proc.returncode == 0, stdout_output, stderr_output

def collect_results(hostname):
    for experiment_dir in DIR.glob("0*"):
        if not experiment_dir.is_dir():
            continue
        subprocess.run(["rsync", "-ahP", "--info=progress2", f"{hostname}:~/hoedur-experiments/{experiment_dir.name}/results/fuzzing-runs/", DIR / f"{experiment_dir.name}/results/fuzzing-runs/"])

try:
    check_rsync()
except subprocess.CalledProcessError:
    print("[ERROR] rsync?")
    exit(1)

host_entries = load_available_hosts()

for hostname in host_entries:
    if hostname == "localhost":
        print("[*] Skipping localhost")
        continue

    print(f"[*] Checking host {hostname}")
    success, stdout_output, stderr_output = check_host(hostname)
    if success:
        print("[+] Check passed")
    else:
        print(f"[ERROR] Got command output for 'ssh {hostname} ls hoedur-experiments':")
        print(f"Stdout: {stdout_output.decode()}")
        print(f"Stderr: {stderr_output.decode()}")
        exit(1)

for hostname in host_entries:
    print(f"Collecting results from {hostname}")
    collect_results(hostname)
