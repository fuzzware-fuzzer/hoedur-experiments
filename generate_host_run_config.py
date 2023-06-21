#!/usr/bin/env python3

import argparse
import datetime
import glob
import math
import os
import subprocess
import yaml

from typing import Dict

from pathlib import Path
from scripts.eval_data_processing.config import EXPERIMENTS, BASEDIR, parse_duration

FUZZER_TYPES = ['hoedur', 'fuzzware']
MAX_FUZZER_NAME_LEN = max([len(n) for n in FUZZER_TYPES])

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", default=False, action="store_true", help="Upload the configurations to the respective hosts.")

    return parser

def load_available_hosts() -> Dict[str, int]:
    hosts = {}

    path = BASEDIR / 'experiment-config' / 'available_hosts.txt'
    for line in open(path).readlines():
        # skip emtpty lines
        if len(line.strip()) == 0:
            continue

        # collect host + cores
        [host, cores] = line.split(maxsplit=2)
        cores = int(cores)

        if host in hosts:
            print(
                f"WARNING: hostname {host} specified multiple times, skipping.")
            continue

        print(f'Found available host "{host}" with {cores} cores')
        hosts[host] = cores

    return hosts


def by_duration(item):
    return parse_duration(item[1]['duration'])


def collect_runs():
    run_list = []

    # sort experiments by duration descending (long experiments first)
    experiments = sorted(EXPERIMENTS.items(), key=by_duration, reverse=True,)

    for name, experiment in experiments:
        duration = experiment['duration']
        runs = experiment['runs']
        cores = 1
        if 'cores' in experiment:
            cores = experiment['cores']

        for fuzzer in experiment['fuzzer']:
            # re-use previous fuzzing run for suitable experiments
            if 'symlink_fuzzer' in experiment and fuzzer in experiment['symlink_fuzzer']:
                continue

            for target in experiment['target']:
                for run_id in range(runs):
                    run_list.append({
                        'output': name,
                        'fuzzer': fuzzer,
                        'target': target,
                        'run_id': run_id + 1,
                        'cores_per_run': cores,
                        'duration': duration,
                    })

    return run_list


def create_run_config(run_list):
    hosts = load_available_hosts()

    # sanity check: host cores >= cores_per_run
    min_host_cores = max([run['cores_per_run'] for run in run_list])
    for host, cores in hosts.items():
        if cores < min_host_cores:
            print(
                f'WARNING: host "{host}" has less than {min_host_cores} cores and is not suitable for all configured experiments')

    # core baseline
    sum_cores = sum(hosts.values())
    print(f'Found {sum_cores} total available cores on {len(hosts)} host(s)')

    # collect duration / fuzzer type
    duration_hoedur = 0
    duration_fuzzware = 0
    for run in run_list:
        duration = parse_duration(run['duration'])
        if 'hoedur' in run['fuzzer']:
            duration_hoedur += duration
        elif 'fuzzware' == run['fuzzer']:
            duration_fuzzware += duration
        else:
            print(f'ERROR: unknown fuzzer "{run["fuzzer"]}"')
            exit(1)

    # split cores between fuzzers
    scale_h_f = duration_hoedur / sum([duration_hoedur, duration_fuzzware])
    cores_hoedur = math.floor(sum_cores * scale_h_f)
    cores_fuzzware = math.ceil(sum_cores * (1 - scale_h_f))
    # make use of remaining cores
    if cores_hoedur < cores_fuzzware:
        cores_unused = (cores_fuzzware % min_host_cores)
        cores_hoedur += cores_unused
        cores_fuzzware -= cores_unused
    else:
        cores_unused = (cores_hoedur % min_host_cores)
        cores_hoedur -= cores_unused
        cores_fuzzware += cores_unused
    print(
        f'Try to split cores bases on experiment runtime: {cores_hoedur} core(s) for Hoedur, {cores_fuzzware} core(s) for Fuzzware')
    if min([cores_hoedur, cores_fuzzware]) < min_host_cores:
        if cores_hoedur + cores_fuzzware < min_host_cores:
            print(
                f'ERROR: less than {min_host_cores} core(s) is not suitable for configured experiments')
            exit(1)
        else:
            print(
                f'WARNING: less than {min_host_cores} core(s) are available when splitting Hoedur and Fuzzware cores.')
            print(
                f'WARNING: Running the experiments will fall back to running sequentially. This may make experiments take longer.')

    # create run configs
    run_config = {}
    for host, cores in hosts.items():
        # assign fuzzware cores
        fuzzware = min(cores_fuzzware, cores)
        fuzzware -= fuzzware % min_host_cores
        cores_fuzzware -= fuzzware

        # assign hoedur cores
        hoedur = min(cores_hoedur, cores - fuzzware)
        hoedur -= hoedur % min_host_cores
        cores_hoedur -= hoedur

        run_config[host] = {
            'cores': {
                'hoedur': hoedur,
                'fuzzware': fuzzware,
            },
            'runs': []
        }

    if cores_fuzzware + cores_hoedur > 0:
        print(
            f'WARNING: could not use {cores_fuzzware} Fuzzware core(s) + {cores_hoedur} Hoedur core(s) due to configured `cores_per_run` in experiment run profile')

    return run_config


def next_run(run_list, fuzzer):
    for i in range(len(run_list)):
        if fuzzer in run_list[i]['fuzzer']:
            return i

    return None


def schedule_runs(run_list, config, max_duration, fuzzer):
    runs = []
    cores = config['cores'][fuzzer]
    max_duration = max_duration[fuzzer]

    while cores > 0:
        # get next run (sorted by duration)
        run_index = next_run(run_list, fuzzer)
        if run_index is None:
            break
        run = run_list[run_index]
        run_duration = parse_duration(run['duration'])

        # reserve core(s)
        cores -= run['cores_per_run']

        # use available duration (multiple runs per chunk when duration < max_duration)
        used_duration = 0
        while used_duration + run_duration <= max_duration:
            # reserve duration
            used_duration += run_duration

            # push next run
            runs.append(run_list.pop(run_index))

            # get next run
            run_index = next_run(run_list, fuzzer)
            if run_index is None:
                break
            run = run_list[run_index]
            run_duration = parse_duration(run['duration'])

    return runs

def check_rsync():
    subprocess.check_output(["rsync", "-h"])

def check_host(hostname):
    proc = subprocess.Popen(["ssh", hostname, "ls", "hoedur-experiments"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_output, stderr_output = proc.communicate()
    return proc.returncode == 0, stdout_output, stderr_output

def upload_config(hostname):
    local_config_path = BASEDIR / 'experiment-config' / 'host-run-configs' / f'{hostname}.yml'
    remote_config_path = os.path.join("~", 'hoedur-experiments', 'experiment-config', 'host-run-configs')

    subprocess.run(["rsync", "-ahP", "--info=progress2", local_config_path, f"{hostname}:{remote_config_path}"])

def try_upload(run_config):
    try:
        check_rsync()
    except subprocess.CalledProcessError:
        print("[ERROR] rsync?")
        exit(1)

    # upload host run config
    for hostname, _ in run_config.items():
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

    for hostname, _ in run_config.items():
        upload_config(hostname)

def main():
    parser = create_parser()
    args = parser.parse_args()

    # verify no previous run config is available
    config_path = BASEDIR / 'experiment-config' / 'host-run-configs'
    old_files = glob.glob(f'{config_path}/*.yml')
    if len(old_files) > 0:
        old_file_list = '\n\t- '.join(old_files)
        print(
            f'ERROR: Old host run config files are present:\n\t- {old_file_list}')
        print(f'Please clean old config / experiment files!')
        print('NOTE: see "./experiment-config/host-run-configs/"')

        do_exit = True
        if args.upload:
            resp = input(f"\nWould you like to re-generate and upload anyways (yes/no)? ").lower()
            if resp == "yes":
                do_exit = False
            else:
                print("Chose not to upload anyways, exiting...")

        if do_exit:
            exit(1)

    # collect runs / host config
    run_list = collect_runs()
    run_config = create_run_config(run_list)

    overall_max_duration = 0
    # schedule runs
    while len(run_list) > 0:
        deadlock = True

        # get next chunk duration
        max_duration = {}
        for fuzzer in FUZZER_TYPES:
            run_index = next_run(run_list, '')
            if run_index is None:
                duration = 0
            else:
                duration = parse_duration(run_list[run_index]['duration'])

            overall_max_duration = max(overall_max_duration, duration)
            max_duration[fuzzer] = duration

        # collect next schedule chunk
        for host, config in run_config.items():
            runs = []
            for fuzzer in FUZZER_TYPES:
                runs += schedule_runs(run_list, config, max_duration, fuzzer)
            config['runs'] += runs

            if len(runs) > 0:
                deadlock = False

        if deadlock:
            print(config['runs'])
            print(
                f'ERROR: could not find suitable host for remaining runs: {run_list}')
            print(
                f'ERROR: Got deadlock during scheduling. Exiting...')
            exit(1)

    max_run_time = 0
    max_run_time_host = ""
    # calculate approximate duration
    for host, config in run_config.items():
        print(f"\n=== Parallel scheduling on {host}")
        for i, fuzzer in enumerate(FUZZER_TYPES):
            cores = config['cores'][fuzzer]
            runs = [run for run in config['runs'] if fuzzer in run['fuzzer']]
            if cores == 0:
                assert len(runs) == 0
                continue

            sum_cores = sum([run['cores_per_run'] for run in runs])
            sum_duration = sum([parse_duration(run['duration']) * run['cores_per_run']
                               for run in runs])
            est_seconds = (sum_duration / cores)
            wallclock = datetime.timedelta(
                seconds=est_seconds)
            print(
                f"{fuzzer.ljust(MAX_FUZZER_NAME_LEN)}: {cores} cores. {len(runs)} experiments ({sum_cores} experiment cores). Estimated time: {wallclock}.")
            if max_run_time < est_seconds:
                max_run_time_host = host
                max_run_time = est_seconds

    max_time_delta = datetime.timedelta(
        seconds=max_run_time)
    print(f"\nOverall, host {max_run_time_host} has the longest estimated time of {max_time_delta}.")

    max_overall_duration_time_delta = datetime.timedelta(
        seconds=overall_max_duration)
    print(f"\nNOTE (1): Approximated wall-clock time is the average experiment duration per core, this does not necessarily correspond to actual wall-clock duration. Due to experiment distribution this can take up to max experiment duration ({max_overall_duration_time_delta}) longer.")
    print(f"NOTE (2): Also, an additional overhead is introduced on each host to perform some local post-processing such as collecting code coverage.")

    OVERHEAD_ESTIMATE = 0.20
    conservative_estimate_time_delta = datetime.timedelta(
        seconds=(max_run_time + overall_max_duration) * (1 + OVERHEAD_ESTIMATE))
    print(f"\nIncluding {round(OVERHEAD_ESTIMATE * 100)}% overhead (for local post-processing) and including the potential delta, the fuzzing runs should be finished within between {max_time_delta} and {conservative_estimate_time_delta}")

    # write host run config
    for host, config in run_config.items():
        path = config_path / f'{host}.yml'
        open(path, 'w').write(yaml.safe_dump(config))

    # upload if so requested
    if args.upload:
        try_upload(run_config)


if __name__ == '__main__':
    main()
