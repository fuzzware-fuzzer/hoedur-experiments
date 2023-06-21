#!/usr/bin/env python3

"""
Find interesting targets (to decide which plots should be in the main body and which should be in the Appendix)
"""

from statistics import mean
from typing import Dict, List

from config import EXPERIMENTS
from parsing import parse_data


RUNTIME = 1 * 24 * 3600


def get_rounded_factor(baseline: float, tweak: float) -> float:
    factor = round(tweak / baseline, 2)
    return factor


def stringify_factor(factor: float) -> str:
    factor_str = f"{factor:.2f}"
    return factor_str


def compare_coverage(data: Dict[str, Dict[str, List[int]]], baseline: str, tweak: str) -> None:
    print(f"## baseline={baseline}, tweak={tweak}")
    baseline_covs: List[float] = []
    tweak_covs: List[float] = []
    percentages: List[float] = []
    for target, target_data in data.items():
        assert len(target_data[baseline]) == len(target_data[tweak]), \
                f"Missing data points: {len(target_data[baseline])} ({baseline}) vs {len(target_data[tweak])} ({tweak}) for target {target}"
        # mean over the N runs
        target_baseline_mean = mean(target_data[baseline])
        target_tweak_mean = mean(target_data[tweak])
        # calculate same stats
        target_factor = get_rounded_factor(target_baseline_mean, target_tweak_mean)
        target_percentage = round(100 * (target_tweak_mean - target_baseline_mean) / target_baseline_mean, 2)
        print(
            f"{target:34}: mean({baseline})={target_baseline_mean:7}, mean({tweak})={target_tweak_mean:7} " \
            f"-> factor: {target_factor:>6} -- {target_percentage:6}% better"
        )
        baseline_covs.append(target_baseline_mean)
        tweak_covs.append(target_tweak_mean)
        percentages.append(target_percentage)
    assert len(baseline_covs) == len(tweak_covs), f"Missing coverage data: {len(baseline_covs)} ({baseline}) vs {len(tweak_covs)} ({tweak})"
    # average over our targets
    baseline_mean = mean(baseline_covs)
    tweak_mean = mean(tweak_covs)
    factor_str = get_rounded_factor(baseline_mean, tweak_mean)
    print(
        f"{'mean over all targets':34}: mean({baseline})={baseline_mean:7}, mean({tweak})={tweak_mean:7} " \
        f"-> factor: {factor_str:>6}"
    )
    print(f"mean_factor={factor_str}")
    improvement = 100 * (tweak_mean - baseline_mean) / baseline_mean
    # sanity-check
    improvement_alt = 100 * (sum(tweak_covs) / sum(baseline_covs) - 1)
    if round(improvement, 6) != round(improvement_alt, 6):
        print(f"[WARNING] {improvement} vs {improvement_alt} (diff: {abs(improvement - improvement_alt)})")
    print(f"avg improvement of tweak over baseline: {improvement:.2f}% (min. improvement: {min(percentages)}%, max. improvement: {max(percentages)}%)")

    print()


def print_other_data() -> None:
    # comparison of coverage for all other datasets
    experiment = EXPERIMENTS["02-coverage-est-data-set"]
    target_to_fuzzer_to_bbs = parse_data(experiment)
    compare_coverage(target_to_fuzzer_to_bbs, baseline="fuzzware", tweak="hoedur")
    compare_coverage(target_to_fuzzer_to_bbs, baseline="fuzzware", tweak="hoedur-single-stream")
    compare_coverage(target_to_fuzzer_to_bbs, baseline="hoedur-single-stream", tweak="hoedur")



def print_cve_data() -> None:
    # comparison of coverage for Fuzzware's CVE dataset
    experiment = EXPERIMENTS["01-bug-finding-ability"]
    target_to_fuzzer_to_bbs = parse_data(experiment)
    compare_coverage(target_to_fuzzer_to_bbs, baseline="fuzzware", tweak="hoedur")


def print_dict_data() -> None:
    # comparison of coverage for the dictionary dataset
    experiment = EXPERIMENTS["03-advanced-mutations"]
    target_to_fuzzer_to_bbs = parse_data(experiment)
    compare_coverage(target_to_fuzzer_to_bbs, baseline="hoedur-single-stream", tweak="hoedur-single-stream-dict")
    compare_coverage(target_to_fuzzer_to_bbs, baseline="hoedur", tweak="hoedur-dict")



def main() -> None:
    print("# Data for Fuzzware's CVE dataset\n")
    print_cve_data()

    print("\n"*3)
    print("-"*120)
    print("\n"*3)

    print("# Data for other datasets\n")
    print_other_data()

    print("\n"*3)
    print("-"*120)
    print("\n"*3)

    print("# Data for Dictionary targets\n")
    print_dict_data()


if __name__ == "__main__":
    main()
