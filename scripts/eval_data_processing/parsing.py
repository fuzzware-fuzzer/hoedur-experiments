#!/usr/bin/env python3

"""
Parsing helper methods
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import json
import zstandard as zst

from config import parse_duration


def get_last_y_val(data: Dict[int, int], timeout: int) -> int:
    """
    In dict that maps x: y, find the last y val before/at RUNTIME
    In other words, find last updated y value (i.e., basic block number)
    before the RUNTIME ran out (needed as sometimes we want a shorter runtime
    than recorded)
    """
    while timeout:
        y_val = data.get(timeout, None)
        if y_val is not None:
            return y_val
        timeout -= 1
    return 0


def parse_raw_data(files: List[Path]) -> list[Dict[int, int]]:
    decompressor = zst.ZstdDecompressor()
    xy_mapping_sorted_all: List[Dict[int, int]] = []
    for f in files:
        decompressed = decompressor.decompress(
            f.read_bytes(), max_output_size=1024*1024*1024*10)
        data = json.loads(decompressed)["coverage_translation_blocks"]
        xy_mapping = {e["x"]: e["y"] for e in data}
        xy_mapping_sorted = dict(
            list(sorted(xy_mapping.items(), key=lambda e: e[0])))  # type: ignore
        xy_mapping_sorted_all.append(xy_mapping_sorted)
    return xy_mapping_sorted_all


def parse_data(experiment: Dict[str, Any]) -> Dict[str, Dict[str, List[int]]]:
    # load fuzzer and target names from the experiment
    fuzzers: List[str] = experiment["fuzzer"]
    targets: List[str] = experiment["target"]

    # load the location of data files from plots.json file
    base_path = Path(experiment["path"]) / "results" / "coverage"
    with open(base_path / "plots.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)
    assert "data" in data, "Failed to find 'data' as key in plots.json"
    data = data["data"]

    target_to_fuzzer_to_bbs: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
    for fuzzer in fuzzers:
        for target in targets:
            assert fuzzer in data, f"Failed to find {fuzzer} as key in plots.json['data']"
            assert target in data[fuzzer], f"Failed to find {target} as key in plots.json['data']['{fuzzer}']"
            paths = [base_path / Path(p) for p in data[fuzzer][target].values()]

            raw_cov_data = parse_raw_data(paths)
            last_y_vals = [get_last_y_val(d, parse_duration(experiment["duration"])) for d in raw_cov_data]
            # FIXME: use this assert once non-model runs are removed
            # num_runs = experiment["runs"]
            # assert len(last_y_vals) == num_runs, f"Found data for {len(last_y_vals)} runs (expected {num_runs})"
            target_to_fuzzer_to_bbs[target][fuzzer] = last_y_vals

    return target_to_fuzzer_to_bbs
