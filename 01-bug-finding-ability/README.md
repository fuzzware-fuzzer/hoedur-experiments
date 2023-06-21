# Bug Finding Ability

This experiment checks the ability of different Fuzzers to generate code coverage and trigger bugs in
the targets previously published by [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/tree/main/03-fuzzing-new-targets).

# Running the Experiment

To run the experiment, refer to [../generate_host_run_config.py](../generate_host_run_config.py). Based on a description of the hosts that are available to run the experiments, this utility generates scripts that can be distributed to the available hosts to split the overall workload and allow for a more time efficient reproduction.

# Interpreting the Results

With the main objective of this experiment being the bug detection timings of different fuzzers, the main result data is located in the following places:

1. [./results/bug-discovery-timings](./results/bug-discovery-timings) contains the raw data on bug discovery timings. `./results/bug-discovery-timings/timings.txt` will contain the numbers in human-readable form.
2. [table_1_cve_discovery_timings.tex](./results/table_1_cve_discovery_timings.tex) and [table_2_add_bugs_discovery_timings.tex](./results/table_2_add_bugs_discovery_timings.tex) which represent Table 1 and Table 2 in the paper. They show the discovery timings of the different bugs in LaTeX table form.

The expectation here is that Hoedur discovers bugs more quickly overall than the reference fuzzers.