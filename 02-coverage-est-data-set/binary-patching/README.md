# Patches to the established Firmware Data Set

This directory contains binary patches to the target set which was first used in this form in the [uEmu paper](https://github.com/MCUSec/uEmu-real_world_firmware). We applied patches to these targets as they contain easy-to-trigger bugs which allow user input to obtain control of the program counter (RIP control) and achieve arbitrary code execution. This causes code coverage comparisons to become invalid, as fuzzers are able to generate random, invalid coverage.

To enable a valid code coverage comparison in these targets, we removed the corresponding known bugs from the firmware targets via binary patches. We chose to apply binary patches for two reasons: First, the exact source code is not available for all targets of the data set. Second, binary patches introduce as little differences as possible in the binary representation of the original.

To make sure the binary patches are easy to understand and verify, we take two steps:
1. We chose a configuration format which contains the specification of the actual binary patch, as well as a textual description of each patch.
2. We provide READMEs which contain information on each bug that we considered during our binary patching efforts.

## Directory Structure

| Path | Description |
| --   | --          |
| [patches](patches) | YAML-based binary patching configuration / description files. |
| [WYCINWYC_patching_notes.md](WYCINWYC_patching_notes.md) | Details about the bugs contained in the "What you corrupt is not what you crash" (WYCINWYC) data set. |
| [uEmu_patching_notes.md](uEmu_patching_notes.md) | Details about the bugs contained in the uEmu data set. |
| [Pretender_patching_notes.md](Pretender_patching_notes.md) | Details about the bugs contained in the PRETENDER data set. |
| [P2IM_patching_notes.md](P2IM_patching_notes.md) | Details about the bugs contained in the P2IM data set. |
| [HALucinator_patching_notes.md](HALucinator_patching_notes.md) | Details about the bugs contained in the HALucinator data set. |
