# Previously Unknown Bugs Found by Hoedur

This directory contains all information required to reproduce our fuzzing targets regarding the previously unknown bugs that Hoedur detected. The directory holds the following components:

1. References to Firmware targets (prebuilt binaries and build environment)
2. Scripts to run the fuzzer against the targets newly introduced by hoedur
3. Details on the bugs found by Hoedur
4. Pre-generated POC inputs that trigger each CVE bug

# Running the Experiment

In this repository we provide pre-extracted bug reproducer inputs under [./results/bug-reproducers](./results/bug-reproducers). These are also linked to in the tables below.
The script [run_reproducer.py](./scripts/run_reproducer.py) can be used to execute the reproducing input in Hoedur. To run the script execute this command:
```
./scripts/run_reproducer.py <bug_name>
```
Where `bug_name` is the name of the reproducer in the table [Bug Overview](#bug-overview), e.g., `CVE-2023-31129`.
Additional options are `--results` to pass a custom `bug-reproducers` directory, `--targets` to pass a custom `targets` directory, and `--trace` to show additional execution trace information.
E.g., to execute an input from experiment [01-bug-finding-ability](../01-bug-finding-ability) run:
```
./scripts/run_reproducer.py --results ../01-bug-finding-ability/results/bug-reproducers <bug_name>
```
After the execution finishes a register dump and the crash reason for the bug are printed.

For convenience scripts to run each reproducer are located in [repro-run-scripts](./repro-run-scripts).
Additionally for each reproducer a README is provided that describes how the emulator output can be interpreted and why this input leads to a given crash.

To rerun the experiment, refer to [../generate_host_run_config.py](../generate_host_run_config.py). Based on a description of the hosts that are available to run the experiments, this utility generates scripts that can be distributed to the available hosts to split the overall workload and allow for a more time efficient reproduction.

# Target Overview
This table contains information on the fuzzing target. Note that some of the new CVEs found by Hoedur were identified while fuzzing targets from the [Fuzzware data set](../targets/arm/Fuzzware) (for reference, see also the [originally published Fuzzware experiment data](https://github.com/fuzzware-fuzzer/fuzzware-experiments/tree/main/03-fuzzing-new-targets)).

| CVE            | OS / Lib                                               | Build Script                               | Prebuilt Target   |
| ---            | --                                                     | --                                         | ------            |
| CVE-2023-23609 | [Contiki-NG](https://github.com/contiki-ng/contiki-ng) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/contiki-ng/building/build_sample_CVE-2020-12140.sh) | [Firmware](../targets/arm/Fuzzware/contiki-ng/CVE-2020-12140)  |
| CVE-2023-28116 | [Contiki-NG](https://github.com/contiki-ng/contiki-ng) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/contiki-ng/building/build_sample_CVE-2020-12140.sh) | [Firmware](../targets/arm/Fuzzware/contiki-ng/CVE-2020-12140)  |
| CVE-2023-29001 | [Contiki-NG](https://github.com/contiki-ng/contiki-ng) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/contiki-ng/building/build_sample_CVE-2020-12140.sh) | [Firmware](../targets/arm/Fuzzware/contiki-ng/CVE-2020-12140)  |
| CVE-2023-31129 | [Contiki-NG](https://github.com/contiki-ng/contiki-ng) | [build.py](./building/contiki-ng/build.py) | [Firmware](../targets/arm/Hoedur/contiki-ng/CVE-2023-31129)    |
| CVE-2022-41873 | [Contiki-NG](https://github.com/contiki-ng/contiki-ng) | [build.py](./building/contiki-ng/build.py) | [Firmware](../targets/arm/Hoedur/contiki-ng/CVE-2022-41873)    |
| CVE-2022-41972 | [Contiki-NG](https://github.com/contiki-ng/contiki-ng) | [build.py](./building/contiki-ng/build.py) | [Firmware](../targets/arm/Hoedur/contiki-ng/CVE-2022-41972)    |
| CVE-2023-0397 | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/zephyr-os/building/build_sample_CVE-2021-3329.sh) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2021-3329)    |
| CVE-2023-1422 | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/zephyr-os/building/build_sample_CVE-2021-3329.sh) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2021-3329)    |
| CVE-2023-1423 | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/zephyr-os/building/build_sample_CVE-2021-3329.sh) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2021-3329)    |
| CVE-2023-1901 | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/zephyr-os/building/build_sample_CVE-2021-3329.sh) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2021-3329)    |
| CVE-2023-1902 | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/zephyr-os/building/build_sample_CVE-2021-3329.sh) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2021-3329)    |
| CVE-2023-0359 [\*](#*-cve-2023-0359-note) | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [Fuzzware](https://github.com/fuzzware-fuzzer/fuzzware-experiments/blob/main/03-fuzzing-new-targets/zephyr-os/building/build_sample_CVE-2020-10064.sh) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2020-10064)  |
| CVE-2022-3806 | [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | [build.py](./building/zephyr-os/build.py) | [Firmware](../targets/arm/Fuzzware/zephyr-os/CVE-2022-3806)    |
| CVE-2023-24817 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24817) |
| CVE-2023-24818 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24818) |
| CVE-2023-24819 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24819) |
| CVE-2023-24820 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24820) |
| CVE-2023-24821 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24821) |
| CVE-2023-24822 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24822) |
| CVE-2023-24823 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24823) |
| CVE-2023-24825 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24825) |
| CVE-2023-24826 | [RIOT](https://github.com/RIOT-OS/RIOT) | [build.py](./building/riot/build.py) | [Firmware](../targets/arm/Hoedur/riot/CVE-2023-24826) |
| CVE-2022-39274 | [LoRaMac-node](https://github.com/Lora-net/LoRaMac-node) | [build.py](./building/loramac-node/build.py) | [Firmware](../targets/arm/Hoedur/loramac-node/CVE-2022-39274)    |

# Bug Overview
This table contains information on the bugs found by Hoedur. Note that some of the new CVEs found by Hoedur were identified while fuzzing targets from the [Fuzzware CVE data set](../targets/arm/Fuzzware) (for reference, see also the [original published experiment data](https://github.com/fuzzware-fuzzer/fuzzware-experiments/tree/main/03-fuzzing-new-targets)). As a result, some POC inputs are located in the results of experiment [01-bug-finding-ability](../01-bug-finding-ability).

| CVE ID         | Details                                               | Fix                   | Bug Reproducer Input  |
| ---            | -------                                               | ---                   | ---                   |
| CVE-2023-23609 | [writeup](./bug-details/contiki-ng/CVE-2023-23609-bt_l2cap_sdu_length_OOB.md) | [contiki-ng/pull/2254](https://github.com/contiki-ng/contiki-ng/pull/2254) | [new-Bug-unchecked_sdu_length](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/contiki-ng/CVE-2020-12140/new-Bug-unchecked_sdu_length) |
| CVE-2023-28116 | [writeup](./bug-details/contiki-ng/CVE-2023-28116-ble-mac_config-OOB.md) | [contiki-ng/pull/2398](https://github.com/contiki-ng/contiki-ng/pull/2398) | [new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/contiki-ng/CVE-2020-12140/new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write) |
| CVE-2023-29001 | [writeup](./bug-details/contiki-ng/CVE-2023-29001-ipv6_routing_header_recursion.md) | [contiki-ng/pull/2264](https://github.com/contiki-ng/contiki-ng/pull/2264) | [new-Bug-ipv6_routing_infinite_recursion](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/contiki-ng/CVE-2020-12140/new-Bug-ipv6_routing_infinite_recursion) |
| CVE-2023-31129 | [writeup](./bug-details/contiki-ng/CVE-2023-31129-ipv6_nbr_rs_SLLAO_missing_null_check.md) | [contiki-ng/pull/2271](https://github.com/contiki-ng/contiki-ng/pull/2271) | [new-Bug-CVE-2023-31129](./results/bug-reproducers/hoedur/Hoedur/contiki-ng/CVE-2023-31129/new-Bug-CVE-2023-31129) |
| CVE-2022-41873 | [writeup](./bug-details/contiki-ng/CVE-2022-41873-bt_l2cap_cid_integer_truncation_OOB.md) | [contiki-ng/pull/2081](https://github.com/contiki-ng/contiki-ng/pull/2081) | [new-Bug-CVE-2022-41873](./results/bug-reproducers/hoedur/Hoedur/contiki-ng/CVE-2022-41873/new-Bug-CVE-2022-41873) |
| CVE-2022-41972 | [writeup](./bug-details/contiki-ng/CVE-2022-41972-bt_l2cap_credit_missing_null_check.md) | [contiki-ng/pull/2253](https://github.com/contiki-ng/contiki-ng/pull/2253) | [new-Bug-CVE-2022-41972](./results/bug-reproducers/hoedur/Hoedur/contiki-ng/CVE-2022-41972/new-Bug-CVE-2022-41972) |
| CVE-2023-0397  | [writeup](./bug-details/zephyr-os/CVE-2023-0397-hci-le_read_buffer_size-DoS.md) | [zephyr/commit/ac3dec5](https://github.com/zephyrproject-rtos/zephyr/commit/ac3dec5) | [new-Bug-invalid-init-le_read_buffer_size](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/zephyr-os/CVE-2021-3329/new-Bug-invalid-init-le_read_buffer_size) |
| CVE-2023-1422  | [writeup](./bug-details/zephyr-os/CVE-2023-1422-hci-sent_cmd-shared-reference-race-condition.md) | TBD | [new-Bug-sent_cmd_shared_ref_race](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/zephyr-os/CVE-2021-3329/new-Bug-sent_cmd_shared_ref_race) |
| CVE-2023-1423  | [writeup](./bug-details/zephyr-os/CVE-2023-1423-hci-isr-invalid-alloc-nullptr.md) | TBD | [new-Bug-hci_prio_event_alloc_err_handling](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/zephyr-os/CVE-2021-3329/new-Bug-hci_prio_event_alloc_err_handling) |
| CVE-2023-1901  | [writeup](./bug-details/zephyr-os/CVE-2023-1901-hci-send_sync-dangling-semaphore-reference-reuse.md) | [zephyr/pull/56709](https://github.com/zephyrproject-rtos/zephyr/pull/56709) | [new-Bug-hci-send_sync-dangling-sema-ref](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/zephyr-os/CVE-2021-3329/new-Bug-hci-send_sync-dangling-sema-ref) |
| CVE-2023-1902  | [writeup](./bug-details/zephyr-os/CVE-2023-1902-hci-connection-creation-dangling-state-reference-reuse.md) | [zephyr/pull/56709](https://github.com/zephyrproject-rtos/zephyr/pull/56709) | [new-Bug-hci-send_sync-dangling-conn-state-ref](../01-bug-finding-ability/results/bug-reproducers/hoedur/Fuzzware/zephyr-os/CVE-2021-3329/new-Bug-hci-send_sync-dangling-conn-state-ref) |
| CVE-2023-0359 [\*](#*-cve-2023-0359-note)  | [writeup](./bug-details/zephyr-os/CVE-2023-0359-ipv6-handle_ra_input-nullptr.md) | [zephyr/pull/53931](https://github.com/zephyrproject-rtos/zephyr/pull/53931) | [new-Bug-ipv6-nullptr](./results/bug-reproducers/hoedur/Fuzzware/zephyr-os/CVE-2020-10064/new-Bug-ipv6-nullptr) |
| CVE-2022-3806  | [writeup](./bug-details/zephyr-os/CVE-2022-3806-hci-send_error_double_free.md) | TBD | [new-Bug-CVE-2022-3806](./results/bug-reproducers/hoedur/Hoedur/zephyr-os/CVE-2022-3806/new-Bug-CVE-2022-3806) |
| CVE-2023-24817 | [writeup](./bug-details/riot/CVE-2023-24817.md) | [RIOT/commit/709ddd2](https://github.com/RIOT-OS/RIOT/commit/709ddd2) | [new-Bug-CVE-2023-24817](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24817/new-Bug-CVE-2023-24817) |
| CVE-2023-24818 | [writeup](./bug-details/riot/CVE-2023-24818.md) | [RIOT/pull/18817](https://github.com/RIOT-OS/RIOT/pull/18817) | [new-Bug-CVE-2023-24818](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24818/new-Bug-CVE-2023-24818) |
| CVE-2023-24819 | [writeup](./bug-details/riot/CVE-2023-24819.md) | [RIOT/pull/18817](https://github.com/RIOT-OS/RIOT/pull/18817) | [new-Bug-CVE-2023-24819](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24819/new-Bug-CVE-2023-24819) |
| CVE-2023-24820 | [writeup](./bug-details/riot/CVE-2023-24820.md) | [RIOT/pull/18817](https://github.com/RIOT-OS/RIOT/pull/18817) | [new-Bug-CVE-2023-24820](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24820/new-Bug-CVE-2023-24820) |
| CVE-2023-24821 | [writeup](./bug-details/riot/CVE-2023-24821.md) | [RIOT/pull/18817](https://github.com/RIOT-OS/RIOT/pull/18817) | [new-Bug-CVE-2023-24821](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24821/new-Bug-CVE-2023-24821) |
| CVE-2023-24822 | [writeup](./bug-details/riot/CVE-2023-24822.md) | [RIOT/pull/18817](https://github.com/RIOT-OS/RIOT/pull/18817) | [new-Bug-CVE-2023-24822](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24822/new-Bug-CVE-2023-24822) |
| CVE-2023-24823 | [writeup](./bug-details/riot/CVE-2023-24823.md) | [RIOT/pull/18817](https://github.com/RIOT-OS/RIOT/pull/18817) | [new-Bug-CVE-2023-24823](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24823/new-Bug-CVE-2023-24823) |
| CVE-2023-24825 | [writeup](./bug-details/riot/CVE-2023-24825.md) | [RIOT/commit/4f1e2a3](https://github.com/RIOT-OS/RIOT/commit/4f1e2a3) | [new-Bug-CVE-2023-24825](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24825/new-Bug-CVE-2023-24825) |
| CVE-2023-24826 | [writeup](./bug-details/riot/CVE-2023-24826.md) | [RIOT/commit/eb9e50a](https://github.com/RIOT-OS/RIOT/commit/eb9e50a) | [new-Bug-CVE-2023-24826](./results/bug-reproducers/hoedur/Hoedur/riot/CVE-2023-24826/new-Bug-CVE-2023-24826) |
| CVE-2022-39274 | [writeup](./bug-details/loramac-node/CVE-2022-39274-ProcessRadioRxDone-payload-oob.md) | [LoRaMac-node/commit/e851b07](https://github.com/Lora-net/LoRaMac-node/commit/e851b079c82ba1bcf3f4d291ab69a571b0bf458a) | [new-Bug-CVE-2022-39274](./results/bug-reproducers/hoedur/Hoedur/loramac-node/CVE-2022-39274/new-Bug-CVE-2022-39274) |

#### \* CVE-2023-0359 Note
The bug corresponding to CVE-2023-0359 was originally found on the Fuzzware target [CVE-2020-10064](../targets/arm/Fuzzware/zephyr-os/CVE-2020-10064).
Originally already an extremely hard bug to trigger, the fuzzer does not seem to produce this bug on a target which is built against the latest version of Zephyr. The reason for this is that an additional layer of complex timing requirements must be satisfied for the bug to be triggered on the latest version of Zephyr.
Thus, we provide a reproducer based on the original Fuzzware target in this directory. Fuzz testing may result in a trigger of CVE-2023-0359 in rare cases of running experiment [01-bug-finding-ability](../01-bug-finding-ability).

# Bug Discovery Example Timings

For reference, we include example timings for the discovery of the new bugs which were found in targets outside the Fuzzware CVE target set. Note that these numbers are not meant to be definitive and may vary based on the number of runs and based on chance.

The bug discovery timings of the new bugs that were found in the [Fuzzware CVE data set](../targets/arm/Fuzzware) can be found in the Hoedur paper or as part of the [results of experiment 01](../01-bug-finding-ability/results) after re-running the experiments.

| CVE ID | Time | Runs |
| ------ | ---- | ---- |
| CVE-2023-31129 | 2h | 17 |
| CVE-2022-41873 | < 30m | 17 |
| CVE-2022-41972 | < 30m | 17 |
| CVE-2023-0359 |  h |    |
| CVE-2022-3806 | 8h | 25 |
| CVE-2023-24817 | 24h | 52 |
| CVE-2023-24818 | < 24h | 5 |
| CVE-2023-24819 | < 24h | 5 |
| CVE-2023-24820 | < 24h | 5 |
| CVE-2023-24821 | < 24h | 5 |
| CVE-2023-24822 | < 24h | 5 |
| CVE-2023-24823 | < 24h | 5 |
| CVE-2023-24825 | 12h | 52 |
| CVE-2023-24826 | < 24h | 5 |
| CVE-2022-39274 | < 30m | 17 |
