# Code Coverage: Established Data Set

In this experiment we tested Hoedur on the established diverse dataset that was also used in previous work.

# Running the Experiment

To run the experiment, refer to [../generate_host_run_config.py](../generate_host_run_config.py). Based on a description of the hosts that are available to run the experiments, this utility generates scripts that can be distributed to the available hosts to split the overall workload and allow for a more time efficient reproduction.

# Interpreting the Results

With the main objective of this experiment being the code coverage of different fuzzers, the main result data is located in the following places:

1. [./results/coverage](./results/coverage) contains the raw data on bug discovery timings. `./results/coverage/summary` will contain the overall covered basic blocks. `./results/coverage/charts` contains (compressed) coverage numbers over time
2. [figure_6_baseline_coverage_plot.pdf](./results/figure_6_baseline_coverage_plot.pdf) and [figure_8_appendix_baseline_coverage_plot.pdf](./results/figure_8_appendix_baseline_coverage_plot.pdf) which represent Figure 6 and Figure 8 in the paper. They show the coverage over time in a plotted form.

The expectation here is that Hoedur is either on par with or achieves a higher coverage than the reference fuzzers, depending on the target.

# Reproducing the Patched Binaries

As described in the paper, we apply patches to many of the targets in the dataset.
We do so to remove any bugs which are known to provide a fuzzer control over the program counter.
This is done so that the program coverage stays comparable by ensuring that no invalid coverage spikes occur due to known bugs.

Currently, the target firmware images allow memory corruptions that give a fuzzer control over the PC.
Although we are typically not counting coverage which was generated from crashing inputs, invalid coverage
can be generated because after a control-flow divergence, fuzzing input can be exhausted and a crash not
triggered. This gives the fuzzer a lot of invalid coverage to chase.

To get around this problem, we are manually binary-patching the firmware images to detect the error conditions
and crash in a controlled and identifiable manner.

The original targets are located in [`unpatched-est-data-set`](/targets/arm/unpatched-est-data-set) and the patches can be found under [`patches`](binary-patching/patches).
Each patch is described in the following documents:

| Dataset | Targets |
| ------- | ------- |
| HALucinator | [6LoWPAN_Receiver](binary-patching/HALucinator_patching_notes.md#6lowpan_receiver) |
| P2IM    | [CNC](binary-patching/P2IM_patching_notes.md#cnc) [Gateway](binary-patching/P2IM_patching_notes.md#gateway) [Heat_Press](binary-patching/P2IM_patching_notes.md#heat_press) [PLC](binary-patching/P2IM_patching_notes.md#plc) [Soldering_Iron](binary-patching/P2IM_patching_notes.md#soldering_iron) |
| Pretender | [RF_Door_Lock](binary-patching/Pretender_patching_notes.md#rf_door_lock) [Thermostat](binary-patching/Pretender_patching_notes.md#thermostat) |
| uEmu    | [GPSTracker](binary-patching/uEmu_patching_notes.md#gpstracker) [utasker_MODBUS](binary-patching/uEmu_patching_notes.md#utasker_modbus) [utasker_USB](binary-patching/uEmu_patching_notes.md#utasker_usb) |
| WYCINWYC | [XML_Parser](binary-patching/WYCINWYC_patching_notes.md#xml_parser) |

Reproducing the binary patching can be done by running:
```sh
./scripts/binary-patching/generate_patched_targets.py
```
The reproduced binaries are place in [patched-binaries](./binary-patching/patched-binaries)

You can check the console output to verify that the reproduced patched binaries match the ones published in the root [`targets`](/targets/arm) directory.

## Patch Template
We use the following template to define patches and make them verifiable:
```
my_patch_name_1:
    description: "Fix OOB bug 1 in function XYZ"
    address: 0x10000abc
    binfile_offset: 0xabc
    patch_contents: "41414141"
my_patch_name_2:
    description: "Fix OBB bug 2 in function XYZ"
    address: 0x10000abc
    binfile_offset: 0xabc
    patch_contents: "42424242"`
```
