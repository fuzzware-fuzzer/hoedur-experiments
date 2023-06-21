#!/usr/bin/env python3

from pathlib import Path
import subprocess

from eval_data_processing.config import EXPERIMENTS, BASEDIR


def git_clean(path):
    try:
        subprocess.check_call(
            ['git', 'clean', '-xdf', path],
            cwd=BASEDIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f'ERROR: failed to clean {path}!\n\t{e}')


def clean_data():
    for name in EXPERIMENTS.keys():
        git_clean(Path(name) / 'results')


def main():
    print('WARNING!')
    print('This will delete all eval data, are you sure?')
    print('Please enter "DELETE" to confirm.')
    line = input('> ')

    if line.strip() != 'DELETE':
        print('Clean aborted!')
        exit(0)

    print('Cleaning, please wait...')
    clean_data()


if __name__ == '__main__':
    main()
