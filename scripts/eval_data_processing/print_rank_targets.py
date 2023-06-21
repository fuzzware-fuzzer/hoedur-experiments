#!/usr/bin/env python3

"""
Rank targets based on max coverage of medians
We use this to decide which plots should be in the main body and which should be in the Appendix
"""

from statistics import median
from typing import Dict, List, Tuple

from config import EXPERIMENTS
from parsing import parse_data


def sort_by_max_coverage(data: Dict[str, Dict[str, List[int]]], length: int = 8) -> None:
    result: List[Tuple[str, float]] = []
    for target, target_data in data.items():
        fuzzer_medians: List[float] = []
        for fuzz_data in target_data.values():
            fuzzer_medians.append(median(fuzz_data))
        result.append((target, max(fuzzer_medians)))

    sorted_result = sorted(result, key=lambda t: t[1], reverse=True)
    for (i, (target, max_med_cov)) in enumerate(sorted_result):
        print(f"{i+1:2}: {target:36} {max_med_cov}")
    selected = {n for n, _ in sorted_result[:length]}
    print(f"First {length} targets (sorted by group/name): {sorted(list(selected), key=lambda k: k.split('/', 1))}")


def main() -> None:
    target_to_fuzzer_to_bbs = parse_data(EXPERIMENTS["02-coverage-est-data-set"])
    # print(target_to_fuzzer_to_bbs)

    print("Sorting targets by maximal coverage (of median):")
    sort_by_max_coverage(target_to_fuzzer_to_bbs)


if __name__ == "__main__":
    main()
