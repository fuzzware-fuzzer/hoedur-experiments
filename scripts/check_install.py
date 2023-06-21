#!/usr/bin/env python3

import os
import subprocess

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))


def check_fuzzware():
    print('Checking fuzzer install...')

    subprocess.check_output([
        DIR / 'fuzzware' / 'run_fuzzware_docker.sh',
        'fuzzware',
        'model',
        '-h',
    ])


def check_hoedur():
    print('Checking hoedur docker...')

    # verify uid/gid matching in docker
    subprocess.check_output([
        DIR / 'run_in_docker.sh',
        'git',
        'status'
    ])

    # verify hoedur is available
    subprocess.check_output([
        DIR / 'run_in_docker.sh',
        'hoedur-arm',
        '--help'
    ])


def check_eval_data_processing():
    print('Checking eval data processing docker...')

    # verify eval data processing docker is available
    subprocess.check_output([
        DIR / 'eval_data_processing' / 'env' / 'run.sh',
        'true'
    ])

    # verify permissions are correct
    subprocess.check_output([
        DIR / 'eval_data_processing' / 'env' / 'run.sh',
        'touch',
        '$BASEDIR/01-bug-finding-ability/results/figure_5_cve_coverage_plot.pdf'
    ])


def main():
    check_fuzzware()
    check_hoedur()
    check_eval_data_processing()


if __name__ == "__main__":
    main()
