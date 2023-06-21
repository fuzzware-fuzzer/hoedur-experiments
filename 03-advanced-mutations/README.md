# Code Coverage: Advanced Mutations via Dictionaries

In this experiment we tested the ability of the multi-stream input representation of Hoedur to support advanced mutations that were previously ineffective when using a flat binary input format. In this case, we added dictionaries (the same option as is available in `AFL` / `AFL++` via the `-x` command-line flag).

# Running the Experiment

To run the experiment, refer to [../generate_host_run_config.py](../generate_host_run_config.py). Based on a description of the hosts that are available to run the experiments, this utility generates scripts that can be distributed to the available hosts to split the overall workload and allow for a more time efficient reproduction.

# Interpreting the Results

With the main objective of this experiment being the code coverage of different fuzzers while using dictionaries, the main result data is located in the following places:

1. [./results/coverage](./results/coverage) contains the raw data on bug discovery timings. `./results/coverage/summary` will contain the overall covered basic blocks. `./results/coverage/charts` contains (compressed) coverage numbers over time
2. [figure_7_baseline_dict_coverage_plot.pdf](./results/figure_7_baseline_dict_coverage_plot.pdf) which represent Figure 7 in the paper. They show the coverage over time in a plotted form.

The expectation here is that Hoedur using dictionaries achieves a higher coverage than the reference fuzzers, even when the same dictionary is used by reference fuzzers.
