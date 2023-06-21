# Target Build Scripts

This directory contains the scripts required to reproduce the new target firmware images that can be found in the provided firmware target [arm/Hoedur](../../targets/arm/Hoedur/) directory.

# Requirements
- Docker
- Python3

To install the required Python packets, run
```
pip install -r requirements.txt
```

# Building Samples
To build the samples, run
```
pip install -r requirements.txt
./rebuild_targets.py
```

Alternatively only a single target can be build with
```
./rebuild_targets.py -t riot -s CVE-2023-24817
```

After running the script, you can find the rebuilt binaries in the [../rebuilt](../rebuilt) directory.

For reference, these rebuilt binaries correspond to the firmware binaries located under [../../targets](../../targets).
