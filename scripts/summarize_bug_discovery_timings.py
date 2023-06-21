#!/usr/bin/env python3
import argparse
import yaml
import json
import os
import pathlib
from glob import glob
from copy import deepcopy

BUG_COMBINATION_YAML_NAME_FORMAT = "bug-combinations-run-{:02d}.yml"
BUG_COMBINATION_PER_FUZZER_SUMMARY_FILENAME = "bug-combinations-min-timings.yml"
FIRST_BUG_COMBINATION_YAML_NAME_FORMAT = BUG_COMBINATION_YAML_NAME_FORMAT.format(1)

MIN_BUG_COMBINATIONS_FILENAME = "bug-combinations-min-timings-single-bug.yml"
UNIQUE_MIN_BUG_COMBINATIONS_FILENAME = "bug-combinations-min-timings-single-bug-exclusive-trigger.yml"
BUG_TIMING_PER_FUZZER_SUMMARY_FILENAME = "summary-per-bug-timings.yml"
UNIQUE_BUG_TIMING_PER_FUZZER_SUMMARY_FILENAME = "summary-per-bug-timings-exclusive-trigger.yml"
BUGNAME_PREFIX_GENERIC = "GENERIC-"
BUGNAME_PREFIX_DUPLICATE = "DUPLICATE-"
BUG_DETECTION_TIMING_SUMMARY_TXT_FILENAME = "timings.txt"
UNIQUE_BUG_DETECTION_TIMING_SUMMARY_TXT_FILENAME = "timings-exclusive-trigger.txt"
BUG_DETECTION_TIMING_SUMMARY_JSON_FILENAME = "timings.json"
UNIQUE_BUG_DETECTION_TIMING_SUMMARY_JSON_FILENAME = "timings-exclusive-trigger.json"

def load_yaml(path):
    print(f"Loading yaml: {path}")
    if not os.path.exists(path):
        print(f"[YAML error] path does not exist {path}")
        return []

    with open(path, 'rb') as infile:
        results = yaml.load(infile, Loader=yaml.FullLoader)

    if not results:
        results = []

    return results

def save_yaml(path, results):
    with open(path, "w") as f:
        f.write(yaml.dump(results))

def save_json(path, results):
    with open(path, "w") as f:
        json.dump(results, f, indent=4)

def collect_bug_combination_files(basedir):
    """
    Collect BugCombination results from a directory where detection timings are placed in the form of
    <path/to/target>/bug-combinations-run-01.yml
    """

    assert(os.path.exists(basedir))

    per_target_results = {}
    for dir_path, _, filenames in os.walk(basedir):
        # Look for bug combination yaml files
        if FIRST_BUG_COMBINATION_YAML_NAME_FORMAT in filenames:
            print(f"Found bug combination file(s) in {dir_path}")
            target_path = str(pathlib.Path(dir_path).relative_to(pathlib.Path(basedir)))
            results_list = per_target_results[target_path] = []

            # Found one, collect them all
            run_no = 1
            yaml_file_path = os.path.join(dir_path, BUG_COMBINATION_YAML_NAME_FORMAT.format(run_no))
            while os.path.isfile(yaml_file_path):
                results_list.append(load_yaml(yaml_file_path))
                run_no += 1
                yaml_file_path = os.path.join(dir_path, BUG_COMBINATION_YAML_NAME_FORMAT.format(run_no))

    return per_target_results

def collect_bug_combinations(discovery_timing_basedir):
    per_fuzzer_results = {}
    for fuzzer_path in glob(discovery_timing_basedir+"/*/"):
        per_fuzzer_results[os.path.split(os.path.dirname(fuzzer_path))[1]] = collect_bug_combination_files(fuzzer_path)

    return per_fuzzer_results

def find_min_per_bug_combination_timings(per_fuzzer_results):
    """ Collect the minimum timings of bug detection for
    - Each bug individually
    - Each combination of detected bugs
    """
    min_timings_per_target = {}

    for target_name, target_run_list in per_fuzzer_results.items():
        curr_min_timings = min_timings_per_target[target_name] = []

        for bug_combination_list in target_run_list:
            min_timings_in_run = {}

            for entry in bug_combination_list:
                """
                entry = [
                    {'BugCombination': bug_combination},
                    {
                        'time': time,
                        'source': {
                            # We are taking liberties in the format here and add an actual path, not an id integer
                            'input': input_path,
                            'report': fuzzware_project_path
                        }
                    }
                ]
                """
                print(f"Trying to unpack entry {entry} into two")
                bug_combination, input_entry = entry

                bugs = tuple(sorted(bug_combination.get('BugCombination', [])))
                if not bugs:
                    continue

                time = input_entry['time']

                curr_entry = min_timings_in_run.setdefault(bugs, entry)

                if curr_entry[1]['time'] > time:
                    min_timings_in_run[bugs] = entry

            # Save only the raw entries, sorted by least number of simultaneously triggered bugs
            curr_min_timings.append(sorted(min_timings_in_run.values(), key=lambda e: len(e[0]['BugCombination'])))

    return min_timings_per_target

def describe_per_fuzzer_minima(unique_bug_names, min_bug_discovery_timings_per_fuzzer, out_txt_path):
    """ Summarizes bug discovery timings into a text representation
    
    Per Fuzzer, we output the timings for the discovery of each bug
    """
    output_text = ""
    for fuzzer_name, bugs_per_target in min_bug_discovery_timings_per_fuzzer.items():
        output_text += f"======== {fuzzer_name} ========\n"

        for target_name, times_per_bug in bugs_per_target.items():
            for bug_name in sorted(times_per_bug.keys()):
                times_to_discovery = times_per_bug[bug_name]
                output_text += f"{target_name}/{bug_name}\t" + " ".join([f"{time:d}" if time is not None else "-" for time in times_to_discovery]) + "\n"
        output_text += "\n\n"
    
    print(output_text)
    with open(out_txt_path, "w") as f:
        f.write(output_text)

def main():
    parser = argparse.ArgumentParser(description="Fuzzware cross-project crash timing gathering")
    def do_help(args, leftover_args):
        parser.parse_args(['-h'])
    parser.set_defaults(func=do_help)

    parser.add_argument('--bug-combination-base-dir', required=True, help="Base directory to search for Fuzzware fuzzing runs (project directories) in. For experiments, this is 'results/fuzzing-runs'. Example: hoedur-experiments/01-bug-finding-ability/results/bug-discovery-timings/fuzzware")

    args = parser.parse_args()
    basedir = args.bug_combination_base_dir

    if not os.path.exists(basedir):
        print(f"[ERROR] Base directory '{basedir}' does not exist")
        exit(1)

    print("Collecting bug combination results...")
    per_fuzzer_results = collect_bug_combinations(basedir)
    per_fuzzer_minimum_timings = {}

    print(f"Collected per-fuzzer results")
    for fuzzer_name, fuzzer_results in per_fuzzer_results.items():
        per_fuzzer_minimum_timings[fuzzer_name] = find_min_per_bug_combination_timings(fuzzer_results)

    # Collect individual bug names along the way
    unique_bug_names = set()

    print("Got minimum timing combinations:")
    for fuzzer_name, fuzzer_minima in per_fuzzer_minimum_timings.items():
        print(f"{fuzzer_name} {fuzzer_minima}")
        save_yaml(os.path.join(basedir, fuzzer_name, BUG_COMBINATION_PER_FUZZER_SUMMARY_FILENAME), fuzzer_minima)

        for target_name, runs in fuzzer_minima.items():
            for run in runs:
                for [bug_combination, input_entry] in run:
                    for bug in bug_combination['BugCombination']:
                        unique_bug_names.add(bug)

    # Now find minima per bug
    print(f"Got unique bugs: {unique_bug_names}")
    # We collect the raw bug combinations with the minimum discovery timing
    min_bug_combinations_per_fuzzer = {}
    unique_min_bug_combinations_per_fuzzer = {}
    # As well as just the raw discovery timings
    #   min_discovery_timing         -> the bug was included in any BugCombination
    min_discovery_timings_per_fuzzer = {}
    #   unique_min_discovery_timings -> only the one bug was triggered (and possibly a related, generic detection hit as well)
    unique_min_discovery_timings_per_fuzzer = {}
    for fuzzer_name, fuzzer_minima in per_fuzzer_minimum_timings.items():
        min_bug_combination_map = min_bug_combinations_per_fuzzer[fuzzer_name] = {}
        unique_min_bug_combination_map = unique_min_bug_combinations_per_fuzzer[fuzzer_name] = {}
        min_timings_per_target = min_discovery_timings_per_fuzzer[fuzzer_name] = {}
        unique_min_timings_per_target = unique_min_discovery_timings_per_fuzzer[fuzzer_name] = {}
        for target_name, runs in fuzzer_minima.items():
            per_run_combinations = min_bug_combination_map[target_name] = []
            unique_per_run_combinations = unique_min_bug_combination_map[target_name] = []

            min_bug_timings = min_timings_per_target[target_name] = {}
            unique_min_bug_timings = unique_min_timings_per_target[target_name] = {}
            for run_no, run in enumerate(runs):
                min_bug_combinations = []
                unique_trigger_min_bug_combinations = []

                for unique_bug_name in unique_bug_names:
                    # Find the entry with the lowest timing which contains the bug
                    bug_combinations_containing_bug = [entry for entry in run if unique_bug_name in entry[0]["BugCombination"]]
                    if not bug_combinations_containing_bug:
                        continue
                    entry = min(
                        bug_combinations_containing_bug
                        , key=lambda entry: entry[1]['time']
                    )
                    bug_timing_entry = deepcopy(entry)
                    bug_timing_entry[0]['BugCombination'] = [unique_bug_name]
                    min_bug_combinations.append(bug_timing_entry)

                    min_bug_timings.setdefault(unique_bug_name, len(runs) * [None])[run_no] = entry[1]['time']

                    # For unique bugs, count only those who only have this specific, non-generic bug entry (or are unique and generic)
                    bug_combinations_containing_only_specific_bug = [entry for entry in bug_combinations_containing_bug
                        if len(entry[0]["BugCombination"]) - 
                            len([1 for bug_name in entry[0]["BugCombination"] if (bug_name.startswith(BUGNAME_PREFIX_DUPLICATE) or bug_name.startswith(BUGNAME_PREFIX_GENERIC)) and bug_name != unique_bug_name]) == 1
                    ]
                    # assert(len(bug_combinations_containing_only_specific_bug) <= 1)
                    if not bug_combinations_containing_only_specific_bug:
                        continue

                    entry = entry = min(
                        bug_combinations_containing_only_specific_bug
                        , key=lambda entry: entry[1]['time']
                    )
                    unique_bug_timing_entry_entry = deepcopy(entry)
                    unique_bug_timing_entry_entry[0]['BugCombination'] = [unique_bug_name]
                    unique_trigger_min_bug_combinations.append(unique_bug_timing_entry_entry)

                    unique_min_bug_timings.setdefault(unique_bug_name, len(runs) * [None])[run_no] = entry[1]['time']

                per_run_combinations.append(min_bug_combinations)
                unique_per_run_combinations.append(unique_trigger_min_bug_combinations)

        save_yaml(os.path.join(basedir, fuzzer_name, MIN_BUG_COMBINATIONS_FILENAME), min_bug_combination_map)
        save_yaml(os.path.join(basedir, fuzzer_name, UNIQUE_MIN_BUG_COMBINATIONS_FILENAME), unique_min_bug_combination_map)

        save_yaml(os.path.join(basedir, fuzzer_name, BUG_TIMING_PER_FUZZER_SUMMARY_FILENAME), min_timings_per_target)
        save_yaml(os.path.join(basedir, fuzzer_name, UNIQUE_BUG_TIMING_PER_FUZZER_SUMMARY_FILENAME), unique_min_timings_per_target)


    save_json(os.path.join(basedir, BUG_DETECTION_TIMING_SUMMARY_JSON_FILENAME), min_discovery_timings_per_fuzzer)
    save_json(os.path.join(basedir, UNIQUE_BUG_DETECTION_TIMING_SUMMARY_JSON_FILENAME), unique_min_discovery_timings_per_fuzzer)

    describe_per_fuzzer_minima(unique_bug_names, min_discovery_timings_per_fuzzer, os.path.join(basedir, BUG_DETECTION_TIMING_SUMMARY_TXT_FILENAME))
    describe_per_fuzzer_minima(unique_bug_names, unique_min_discovery_timings_per_fuzzer, os.path.join(basedir, UNIQUE_BUG_DETECTION_TIMING_SUMMARY_TXT_FILENAME))        

if __name__ == "__main__":
    main()