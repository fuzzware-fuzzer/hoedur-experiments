#!/usr/bin/env python3

import glob
import os
import subprocess

from pathlib import Path

from eval_data_processing.config import EXPERIMENTS, BASEDIR


def test_zstd(path, log=True):
    try:
        subprocess.check_call(
            ['zstd', '-dkfo', '/dev/null', path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=BASEDIR)

        return True
    except Exception as e:
        if log:
            print(f'ERROR: {path} missing / corrupt!\n\t{e}')

        return False


def test_tar_zstd(path, log=True):
    try:
        subprocess.check_call(
            ['zstd', '-dkfo', '/tmp/corpus.tar', path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=BASEDIR)

        subprocess.check_call(
            ['tar', '-tf', '/tmp/corpus.tar'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=BASEDIR)

        return True
    except Exception as e:
        if log:
            print(f'ERROR: {path} missing / corrupt!\n\t{e}')

        return False


def find_unexpected_files(pattern, count):
    matches = glob.glob(str(BASEDIR / pattern))
    found = len(matches)

    if found != count:
        print(
            f'ERROR: Expected to find {count} dirs/files but found {found} dirs/files with pattern "{pattern}"!')
        return False
    else:
        return True


def check_fuzzing_runs_hoedur(name, target, runs, cores, fuzzer, duration):
    fuzzing_dir = Path(name) / 'results' / 'fuzzing-runs' / fuzzer
    target = target.replace('/', '-')
    count = runs * cores
    success = True

    # verify corpus archive, report
    # 01-bug-finding-ability/results/fuzzing-runs/hoedur/01-bug-finding-ability-hoedur/
    # TARGET-Fuzzware-zephyr-os-CVE-2021-3330-FUZZER-hoedur-RUN-10-DURATION-1h-MODE-fuzzware.corpus.tar.zst
    # TARGET-Fuzzware-zephyr-os-CVE-2021-3330-FUZZER-hoedur-RUN-10-DURATION-1h-MODE-fuzzware.report.bin.zst
    corpus_dir = fuzzing_dir / f'{name}-{fuzzer}'
    for run_id in range(count):
        base_filename = f'TARGET-{target}-FUZZER-{fuzzer}-RUN-{run_id + 1:02d}-DURATION-{duration}-MODE-fuzzware'
        archive = corpus_dir / f'{base_filename}.corpus.tar.zst'
        report = corpus_dir / f'{base_filename}.report.bin.zst'

        if not test_tar_zstd(archive):
            # corpus corrupt / missing => skip report check
            success = False
            continue

        if test_zstd(report, log=False):
            # report verified => continue
            continue

        # try to repair
        print('WARNING: Missing / corrupt coverage report found, trying to repair...')
        try:
            from fuzz import do_run_cov
            corpus = str(corpus_dir / f'{base_filename}')
            do_run_cov(archive, fuzzer, target, corpus, False, True)
        except:
            pass

        if test_zstd(report):
            print('INFO: Repair successful!')
        else:
            success = False

    # check no additional (old) runs are there
    success &= find_unexpected_files(
        corpus_dir / f'TARGET-{target}-*.corpus.tar.zst', count)
    success &= find_unexpected_files(
        corpus_dir / f'TARGET-{target}-*.report.bin.zst', count)

    return success


def fuzzware_parse_run_time_log(runtime_log_path):
    """
    Tries to parse the run time log for a fuzzware project dir.

    Returns tuple (planned_runtime_seconds, epoch_start, epoch_end)
    """
    planned_runtime, epoch_start, epoch_end = None, None, None
    if os.path.exists(runtime_log_path):
        with open(runtime_log_path, "r") as f:
            lines = f.readlines()
        planned_runtime = int(lines[0].split(":")[1])
        epoch_start = int(lines[1].split(":")[1])
        if len(lines) >= 3:
            epoch_end = int(lines[2].split(":")[1])

    return planned_runtime, epoch_start, epoch_end


def check_fuzzware_project_runtime(projdir):
    runtime_log_path = os.path.join(projdir, "logs", "runtime.txt")
    if not os.path.exists(runtime_log_path):
        print(
            f'Warning: Fuzzware project {projdir} does not have a runtime log file at logs/runtime.txt')
        return

    planned_runtime, epoch_start, epoch_end = fuzzware_parse_run_time_log(
        runtime_log_path)
    if epoch_end is None:
        print(
            f'Warning: Fuzzware project {projdir} runtime log file does not have an end entry. The run seems to have been forcibly killed.')
        return

    runtime_seconds = epoch_end - epoch_start
    runtime_fraction = runtime_seconds / planned_runtime
    if runtime_fraction < 0.75:
        print(
            f'Warning: Fuzzware project {projdir} runtime log file does not have an end entry. The run seems to have ended prematurely (ran for only {round(100 * runtime_fraction)}% of configured time).')


def check_fuzzing_runs_fuzzware(name, target, runs):
    # 01-bug-finding-ability/results/fuzzing-runs/fuzzware/Fuzzware/contiki-ng/CVE-2020-12140/fuzzware-project-run-01/
    fuzzing_dir = Path(name) / 'results' / 'fuzzing-runs' / 'fuzzware' / target
    pattern = fuzzing_dir / f'fuzzware-project-*'

    fuzzware_projects = glob.glob(str(BASEDIR / pattern))
    for projdir in fuzzware_projects:
        check_fuzzware_project_runtime(projdir)

    return find_unexpected_files(pattern, runs)


def check_fuzzing_runs():
    success = True

    for name, experiment in EXPERIMENTS.items():
        print(f'Checking experiment {name} data...')

        duration = experiment['duration']
        runs = experiment['runs']
        cores = 1
        if 'cores' in experiment:
            cores = experiment['cores']

        for fuzzer in experiment['fuzzer']:
            for target in experiment['target']:
                if 'hoedur' in fuzzer:
                    success &= check_fuzzing_runs_hoedur(
                        name, target, runs, cores, fuzzer, duration)
                else:
                    success &= check_fuzzing_runs_fuzzware(name, target, runs)

    if not success:
        print('ERROR: Some files missing / corrupt, please verify all files are synced correctly.')

    return success


def check_eval_data_hoedur(name, target, runs, cores, fuzzer, duration):
    fuzzing_dir = Path(name) / 'results' / 'fuzzing-runs' / fuzzer
    target = target.replace('/', '-')
    success = True

    # verify merged coverage report
    # 01-bug-finding-ability/results/fuzzing-runs/hoedur/01-bug-finding-ability-hoedur-group/
    # Fuzzware-contiki-ng-CVE-2020-12140-run-1.report.bin.zst
    if cores > 1:
        group_dir = fuzzing_dir / f'{name}-{fuzzer}-group'

        for run_id in range(runs):
            filename = f'TARGET-{target}-RUN-{run_id + 1:02d}.report.bin.zst'

            success &= test_zstd(group_dir / filename)

        success &= find_unexpected_files(
            group_dir / f'TARGET-{target}-*.report.bin.zst', runs)

    return success


def check_eval_data():
    for name, experiment in EXPERIMENTS.items():
        duration = experiment['duration']
        runs = experiment['runs']
        cores = 1
        if 'cores' in experiment:
            cores = experiment['cores']

        for fuzzer in experiment['fuzzer']:
            for target in experiment['target']:
                if 'hoedur' in fuzzer:
                    check_eval_data_hoedur(
                        name, target, runs, cores, fuzzer, duration)
                else:
                    pass


def main():
    success = True
    success &= check_fuzzing_runs()
    # TODO: success &= check_eval_data()

    if not success:
        exit(1)


if __name__ == '__main__':
    main()
