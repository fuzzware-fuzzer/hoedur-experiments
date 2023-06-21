#!/usr/bin/env python3

import os
import subprocess

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))

# Check data
subprocess.check_call([DIR.joinpath("scripts", "run_in_docker.sh"), Path("scripts", "check_data.py")])

# Fuzzware metrics
subprocess.run([DIR.joinpath("scripts", "fuzzware", "run_fuzzware_docker.sh"), Path("scripts", "fuzzware", "generate_all_fuzzware_experiment_metrics.sh")])

# Hoedur metrics
subprocess.run([DIR.joinpath("scripts", "run_in_docker.sh"), Path("scripts", "hoedur-eval.py")])

# Overall metrics
# 1. Summarize bug discovery timings
subprocess.run([DIR.joinpath("01-bug-finding-ability", "scripts", "summarize_bug_discovery_timings.sh")])
# 2. Generate tables and figures
subprocess.run(["make", "-C", DIR.joinpath("scripts", "eval_data_processing")])
# 3. Generate bug discovery timings LaTex tables
subprocess.run([DIR.joinpath("scripts", "eval_data_processing", "print_table_discovery_timings.py")])
