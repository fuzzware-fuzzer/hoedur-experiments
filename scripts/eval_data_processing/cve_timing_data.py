import json
import os

from config import *

timing_in_seconds = {}

# collect timings
for (experiment_name, experiment) in EXPERIMENTS.items():
    basedir = experiment['path']

    path = f'{basedir}/results/bug-discovery-timings/timings.json'
    if not os.path.isfile(path):
        continue

    timing_in_seconds[experiment_name] = json.loads(open(path).read())


def load_data(experiment_name, fuzzer, target, bug):
    data = timing_in_seconds[experiment_name][fuzzer]

    # bug may not be found in _any_ run
    if target in data and bug in data[target]:
        bug_data = data[target][bug]
    else:
        bug_data = [None] * EXPERIMENTS[experiment_name]['runs']

    return bug_data
