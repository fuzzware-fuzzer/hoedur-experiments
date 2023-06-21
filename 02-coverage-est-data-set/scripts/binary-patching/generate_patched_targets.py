#!/usr/bin/env python3
import filecmp
import os
import yaml

from pathlib import Path


def apply_patches(out_path, orig_file_path, patch_entries):
    with open(orig_file_path, "rb") as f:
        contents = f.read()

    # Pre-sort patches to allow multiple appending patches
    ascending_patch_locations = sorted(patch_entries.items(), key=lambda e: e[1]["address"])

    for patch_entry_name, patch_entry in ascending_patch_locations:
        file_offset = patch_entry["binfile_offset"]

        # print(f"Applying patch at offset {file_offset:#x}. Contents: {patch_entry['patch_contents']}")
        patch_contents = bytes.fromhex(patch_entry["patch_contents"])

        # Only allow appending to file or patching in-line. Otherwise, we likely face a wrong file offset
        assert file_offset <= len(contents)
        contents = contents[:file_offset] + patch_contents + contents[file_offset + len(patch_contents) :]

    with open(out_path, "wb") as f:
        f.write(contents)


def load_config(infile_path):
    with open(infile_path, "rb") as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    return config


# colors
GREEN = "\033[92m"
RED = "\033[91m"
ENDC = "\033[0m"

DIR = Path(os.path.dirname(os.path.realpath(__file__)))
UNPATCHED_DIR = DIR.parents[2].joinpath("targets", "arm", "unpatched-est-data-set")
PATCHED_DIR = DIR.parents[2].joinpath("targets", "arm")
REPRODUCED_DIR = DIR.parents[1].joinpath("binary-patching", "patched-binaries")
PATCHES_DIR = DIR.parents[1].joinpath("binary-patching", "patches")

patches = PATCHES_DIR.glob("*/*")
for patch_path in patches:
    dataset, target = patch_path.parts[-2:]
    target = target.replace(".yml", "")

    # get path and name of unpatched bin file
    unpatched_path = UNPATCHED_DIR.joinpath(dataset, target)
    bins = list(unpatched_path.glob("*.bin"))
    assert len(bins) == 1
    unpatched = bins[0]

    patched = PATCHED_DIR.joinpath(*unpatched.parts[-3:])
    reproduced = REPRODUCED_DIR.joinpath(*unpatched.parts[-3:])
    reproduced.parent.mkdir(exist_ok=True, parents=True)
    apply_patches(reproduced, unpatched, load_config(patch_path))
    match = filecmp.cmp(reproduced, patched, shallow=False)

    if match:
        print(GREEN, end="")
    else:
        print(RED, end="")
    print(f"Applying patches to {dataset:15} {target:20} matching binaries {match}")
    print(ENDC, end="")
