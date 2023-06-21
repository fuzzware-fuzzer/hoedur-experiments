#!/usr/bin/env python3

from pathlib import Path
import subprocess

from eval_data_processing.config import EXPERIMENTS


def convert_fuzzware_config(target_dir):
    config = target_dir / 'config.yml'
    config_fuzzware = target_dir / 'config_fuzzware.yml'

    try:
        subprocess.check_output(
            ['hoedur-convert-fuzzware-config', config_fuzzware, config],
            stderr=subprocess.STDOUT)
    except Exception as e:
        print(f'Convert failed for "{config_fuzzware}": {e}')
        return False

    return True


def main():
    targets = Path('targets/arm')
    errors = []

    # convert config
    print(f'Converting Fuzzware config files into Hoedur config files...')
    for experiment in EXPERIMENTS.values():
        # only convert fuzzware config if available
        if not 'fuzzware' in experiment['fuzzer']:
            continue

        for target in experiment['target']:
            result = convert_fuzzware_config(targets / target)

            if result is False:
                errors.append(target)

    # verify if new config differs
    diff = False
    print(f'Diffing newly converted Hoedur config files with checked in version...')
    try:
        subprocess.check_call(
            ['git', '--no-pager', 'diff', '--exit-code', targets], stderr=subprocess.STDOUT)
        print(f'No difference found in newly converted Hoedur config files.')
    except Exception as e:
        print(f'WARNING: Hoedur config file(s) have changed! See stdout/-err for diff.')
        diff = True

    # check for errors
    for target in errors:
        print(
            f'ERROR: Failed to convert Fuzzware config for target {target}!')

    # success
    if len(errors) == 0 and not diff:
        print('All config files converted successfully!')


if __name__ == '__main__':
    main()
