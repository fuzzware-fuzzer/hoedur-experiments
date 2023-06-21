#!/usr/bin/env python3

import os
import threading
import argparse
import yaml

from pathlib import Path

from eval_data_processing.config import BASEDIR

from fuzz_common import *
from fuzz import do_fuzzer_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host_run_config', type=Path)
    parser.add_argument("--cores", default=None, type=int,
                        help="Force the use of a specific number of maximum cores.")
    args = parser.parse_args()

    host_run_config = yaml.safe_load(open(args.host_run_config).read())

    # collect run list
    run_list = []
    for run in host_run_config['runs']:
        # skip non-hoedur fuzzer
        fuzzer = run['fuzzer']
        if not 'hoedur' in fuzzer:
            continue

        # collect arguments
        name = run['output']
        target = run['target']
        cores_per_run = run['cores_per_run']
        run_id = run['run_id']
        duration = run['duration']

        # run a single-core process per core
        for core in range(cores_per_run):
            run_num = (run_id - 1) * cores_per_run + core + 1
            run_list.append(
                [name, run_num, fuzzer, target, duration]
            )

    max = len(run_list)

    # verify cores
    cores = args.cores
    if cores is None:
        cores = host_run_config['cores']['hoedur']
    if len(run_list) > 0 and cores == 0:
        eprint('ERROR: no cores available for run list:\n', run_list)
        exit(1)

    # run in tmp
    os.chdir('/tmp')

    # start thread per core
    threads = []
    for core in range(cores):
        t = threading.Thread(target=runner, args=(core, run_list, max))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def runner(core, run_list, max):
    eprint(core, 'start')

    while len(run_list) > 0:
        # do next fuzzing run
        [name, run_id, fuzzer, target, duration] = run_args = run_list.pop(0)
        print(core, 'run', max - len(run_list), '/', max, ':', run_args)

        try:
            corpus_base = f'{BASEDIR}/{name}/results/fuzzing-runs/{fuzzer}/{name}-{fuzzer}/'
            do_fuzzer_run(corpus_base, target, fuzzer, False, True,
                          True, duration, run_id, False, False, True)
        except CorpusExistsException as e:
            eprint(e)

        eprint(core, 'done', run_args)


if __name__ == '__main__':
    main()
