# Configuring the Experiments

This directory contains information on how to choose experiment durations (the original experiments are rather CPU intensive) and split running the experiments on multiple hosts.

The following is the workflow to pre-configure and run the experiment:

1. Write the desired experiment profile name to [active_profile.txt](active_profile.txt).
2. Configure the available hosts in [available_hosts.txt](available_hosts.txt).
3. Generate the run scripts using [../generate_host_run_config.py](../generate_host_run_config.py). The generated scripts will be located in the [host-run-configs](./host-run-configs) directory.

From there, please refer to the the [root directory README](../README.md) to run the experiments and interpret the results.

# Experiment Profiles

We provide different profiles that allow running the experiment with different degrees of computation requirements:

## Profile Overview

| Profile Name | Description   | CPU Requirement |
| --           | --            | --              |
| `full-eval` | All experiments with their original run times and repetition counts. Requires multiple, high-performance servers as well as considerable amounts of time. | 33 CPU years. Example setup: 30 days of runtime on 8 servers with 50 physical cores each. |
| `test-run` | All experiments with a minimal run-time which allows testing the full experiment pipeline. Can be run on a single, low-power machine. | Few CPU days |
| `shortened-eval` | Experiment run times reduced to amounts that are designed to reproduce our core findings. This still requires considerable computation power, but is more feasible without compute clusters. | 3 CPU years / 1000 CPU days. Example setup: 2 weeks on two servers with 50 physical cores each. |

The profiles are encoded within the experiment profile configuration file at [profiles.yml](./profiles.yml). The profiles can be customized to modify the durations and repetition counts of experiment profiles, or new profiles can be added.

[scripts/eval_data_processing/config.py](scripts/eval_data_processing/config.py) contains more detailed information about the experiments, such as the target binaries that are to be tested and which plots to create. These settings can be used to add an entirely new experiment.

## Profile Details

The following values are pre-defined in [profiles.yml](./profiles.yml):

| Profile Name     | Experiment                | Fuzzing Duration | Repetition Count | Cores per Run |
| --               | --                        | --               | --               | --            |
| `full-eval`      | 01-bug-finding-ability    | 15 days          | 5                | 4             |
|                  | 02-coverage-est-data-set  | 1 day            | 10               | 1             |
|                  | 03-advanced-mutations     | 1 day            | 10               | 1             |
|                  | 04-prev-unknown-vulns     | 1 day            | 52               | 1             |
| `test-run`       | 01-bug-finding-ability    | 1 hour           | 3                | 2             |
|                  | 02-coverage-est-data-set  | 1 hour           | 3                | 1             |
|                  | 03-advanced-mutations     | 1 hour           | 3                | 1             |
|                  | 04-prev-unknown-vulns     | 1 hour           | 3                | 1             |
| `shortened-eval` | 01-bug-finding-ability    | 1 day            | 3                | 4             |
|                  | 02-coverage-est-data-set  | 1 day            | 3                | 1             |
|                  | 03-advanced-mutations     | 1 day            | 3                | 1             |
|                  | 04-prev-unknown-vulns     | 1 day            | 3                | 1             |

For the `shortened-eval`, we opted to increase the runtimes for the two specific targets `CVE-2020-12140` and `CVE-2021-3329` relative to the other targets of the experiment. The reason is that these are the target in which hoedur found additional, previously-unknown bugs, some of which take more time to trigger (see Table 2 in the paper).

# Configuring available Hosts

The available hosts on which the experiments are run can be configured by editing the [available_hosts.txt](available_hosts.txt) file. The file format is the following:

```
<hostname_1> <number_of_cores_to_use_on_host_1>
<hostname_2> <number_of_cores_to_use_on_host_2>
```

> Note: To reproduce the experiments, we highly recommend using hosts with 12 or more cores, as cores are split between Hoedur and Fuzzware execution and Fuzzware requires chunks of multiple cores at a time when using `cores_per_run > 1` (as is the case with experiment `01-bug-finding-ability`). In case you would like to test a short configuration and your local machine has less than the required number of cores according to [../generate_host_run_config.py](../generate_host_run_config.py), you can simply increase the number of cores indicated in [available_hosts.txt](./available_hosts.txt) (or just leave the pre-set 12 core configuration as it is). This will allow you to perform a short experiment test.

The `localhost` name is a special entry which expresses that the experiment is to be run locally and that no syncing of experiment data from a remote host is required for that entry.

Example:
```
localhost 32
my_host_1 16
my_host_2 40
```
