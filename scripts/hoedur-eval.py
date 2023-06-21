#!/usr/bin/env python3

import os
import subprocess

from eval_data_processing.config import EXPERIMENTS

HOEDUR_DIR = '/home/user/hoedur'


def run(args):
    print(args)
    p = subprocess.Popen(args, cwd=HOEDUR_DIR)
    p.wait(None)


def corpus_base_name(fuzzer, experiment_name):
    # experiment_name, e.g. 01-bug-finding-ability
    # fuzzer name, e.g. hoedur-single-stream
    return '-'.join([experiment_name, fuzzer])


def process_run(experiment, fuzzer):
    basedir = experiment['path']
    corpus_name = corpus_base_name(fuzzer, experiment['name'])
    fuzzing_runs_dir = basedir / 'results' / 'fuzzing-runs' / fuzzer
    targets = experiment['target']

    # collect executions
    executions_dir = basedir / 'results' / 'statistics' / 'executions'
    os.makedirs(executions_dir / fuzzer, exist_ok=True)
    run(['scripts/eval-executions.py',
         executions_dir / fuzzer,
         executions_dir / f'{fuzzer}.txt',
         fuzzing_runs_dir / corpus_name,
         '--targets'
         ] + targets)

    # collect bug reproducers
    reproducer_dir = basedir / 'results' / 'bug-reproducers' / fuzzer
    os.makedirs(reproducer_dir, exist_ok=True)
    run(['scripts/eval-bug-reproducer.py',
         reproducer_dir,
         fuzzing_runs_dir / corpus_name,
         '--targets'
         ] + targets)

    # (optional) merge X single-core runs into one group
    if 'cores' in experiment:
        cores = experiment['cores']
        group_name = f'{corpus_name}-group'
        run([
            'scripts/eval-merge-group.py',
            '--output-dir', fuzzing_runs_dir / group_name,
            '--group', str(cores),
            fuzzing_runs_dir / corpus_name,
            '--targets',
        ] + targets)

        # use group corpus for further processing
        corpus_name = group_name

    # collect covered basic blocks:
    # - include only valid basic blocks (`valid_basic_blocks.txt`)
    # - exclude crashing inputs
    # - exclude inputs who trigger an arbitrary code execution bug (even non crashing inputs)
    if 'ace_bugs' in experiment:
        ace_args = ['--filter-bugs']
        for bugs in experiment['ace_bugs'].values():
            ace_args += bugs
    else:
        ace_args = []
    run([
        'scripts/eval-coverage.py',
        basedir / 'results' / 'coverage',
        fuzzing_runs_dir / corpus_name,
        '--fuzzer', fuzzer,
    ] + ace_args + [
        '--targets',
    ] + targets)

    # (optional) collect crash timings:
    # - exclude non crashing inputs
    if 'timings' in experiment:
        run([
            'scripts/eval-bug-combinations.py',
            '--output', basedir / 'results' / 'bug-discovery-timings' / fuzzer,
            fuzzing_runs_dir / corpus_name,
            '--targets',
        ] + targets)


def process_experiment(experiment):
    print(experiment['name'])

    for fuzzer in experiment['fuzzer']:
        if 'hoedur' in fuzzer:
            process_run(experiment, fuzzer)


def main():
    for experiment in EXPERIMENTS.values():
        process_experiment(experiment)


if __name__ == '__main__':
    main()
