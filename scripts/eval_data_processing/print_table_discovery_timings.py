#!/usr/bin/env python3

"""
This script creates the content for a LaTeX table representing the discovery timings
min|max|avg|median
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from statistics import median, mean

from config import EXPERIMENTS, BUG_DESCRIPTION, FUZZER_LATEX, parse_duration
import cve_timing_data

EXPERIMENT_NAME = "01-bug-finding-ability"
EXPERIMENT = EXPERIMENTS[EXPERIMENT_NAME]
TIMEOUT: int = parse_duration(EXPERIMENT["duration"]) # type: ignore
FUZZERS: List[str] = EXPERIMENT["fuzzer"] # type: ignore
NUM_RUNS: int = EXPERIMENT["runs"] # type: ignore

assert isinstance(EXPERIMENT["path"], Path), \
        f"Expected EXPERIMENTS['01-bug-finding-ability']['path'] to be a Path, found {type(EXPERIMENT['path'])}"
TABLE_ONE_PATH = EXPERIMENT["path"] / "results" / "table_1_cve_discovery_timings.tex"
TABLE_TWO_PATH = EXPERIMENT["path"] / "results" / "table_2_add_bugs_discovery_timings.tex"


def load_data(fuzzer: str, target: str, bug: str) -> Tuple[List[Optional[int]], List[int]]:
    bug_data: List[Optional[int]] = cve_timing_data.load_data(EXPERIMENT_NAME, fuzzer, target, bug) # type: ignore

    # if bug not found => use TIMEOUT+1
    assert isinstance(TIMEOUT, int), f"Timeout not an 'int' but {type(TIMEOUT)} (val: {TIMEOUT})"
    clean_data: List[int] = [d if d is not None else TIMEOUT + 1 for d in bug_data]

    return (bug_data, clean_data)


def bug_name_latex(bug: str) -> str:
    # replace bug name with CVE
    if bug in BUG_DESCRIPTION:
        bug = BUG_DESCRIPTION[bug]

    # trim bug/CVE name for table
    bug = bug.replace("CVE-20", "") \
        .replace("new-Bug-","") \
        .replace("fixed-Bug-", "") \
        .replace("_", "\\_") \

    return bug


def time_fmt(seconds: int) -> str:
    """
    Format string into a nice LaTeX table format: dd:hh:mm
    """
    secs = seconds % 60

    rem = (seconds - secs) // 60
    assert rem == (seconds - secs) / 60
    mins = rem % 60
    assert (rem - mins) / 60 == (rem - mins) // 60

    rem = (rem - mins) // 60
    hours = rem % 24
    assert (rem - hours) / 24 == (rem - hours) // 24

    rem = (rem - hours) // 24
    days = rem
    assert days * 24 * 3600 + hours * 3600 + mins * 60 + secs == seconds
    # round to nearest minute
    if secs >= 30:
        mins += 1
    string = f"{days:02}:{hours:02}:{mins:02}"
    # if we hit a timeout, replace this with "---"
    if string == "15:00:00":
        return r"\multicolumn{1}{c}{---}"
    # grey out leading zeroes to improve reading experience
    string = string.replace("00", r"\textcolor{black!40}{00}")
    return string


def get_factor(fuzzer: Union[int, float], baseline: Union[int, float]) -> float:
    """
    Round factor depending on magnitude: 2 digits after comma for small ones, none for large ones
    """
    res = fuzzer / baseline
    if res < 1:
        res = round(res, 2)
    elif res < 10:
        res = round(res, 1)
    else:
        res = round(res)
    return res


def boldify(string: str) -> str:
    return r"\textbf{" + string + r"}"


def base_row(fuzzer: str, data: List[int], orig_data: List[Optional[int]]) -> Tuple[float, str]:
    """
    Build a nice representation of the different values used as a row in the table (excluding target)
    """
    min_s = time_fmt(min(data))
    max_s = time_fmt(max(data))
    mean_val = mean(data)
    mean_s = time_fmt(round(mean_val))
    median_val = round(median(data))
    median_s = time_fmt(median_val)
    run_s = f"{len([e for e in data if e <= TIMEOUT])}/{len(orig_data)}"
    if len([e for e in data if e <= TIMEOUT]) == len(orig_data):
        run_s = boldify(run_s)
    return mean_val, f"{fuzzer:10} & {run_s} & {min_s} & {max_s} & {median_s} & {mean_s}"


def generate_table(timings: Dict[str, Dict[str, List[str]]]) -> str:
    """
    Print a LaTeX table (Table 1 + Table 2) showing the bug discovery timings
    """
    table: List[str] = [r"\arrayrulecolor{black!30}"]
    # baseline here refers to hoedur, which we compare other fuzzers against
    baseline: str = EXPERIMENT["baseline"] # type: ignore
    all_facs: List[Dict[str, float]] = []
    times: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for (target, bugs) in timings.items():
        for bug in bugs:
            rows: Dict[str, str] = {}
            means: Dict[str, float] = {}
            found: Dict[str, int] = {}
            for fuzzer in FUZZERS:
                fuzzer_latex = FUZZER_LATEX[fuzzer]
                (bug_data, clean_data) = load_data(fuzzer, target, bug)
                mean_val, row = base_row(fuzzer_latex, clean_data, bug_data)
                rows[fuzzer] = row
                means[fuzzer] = mean_val
                found[fuzzer] = len(
                    [time for time in bug_data if time is not None]
                )
                # print(f"times[{target}][{bug}][{fuzzer}]={means[fuzzer]}")
                times[fuzzer][target][bug] = mean_val

            facs: Dict[str, float] = {}
            facs_raw: Dict[str, float] = {}
            best_fac = float("inf")
            for fuzzer in FUZZERS:
                facs[fuzzer] = get_factor(means[fuzzer], means[baseline])
                facs_raw[fuzzer] = means[fuzzer] / means[baseline]

                # save best factor (exclude fuzzer without any bug found)
                if found[fuzzer] > 0 and facs_raw[fuzzer] < best_fac:
                    best_fac = facs_raw[fuzzer]
            all_facs.append(facs_raw)

            # find best fuzzer by mean factor
            best_fuzzer: List[str] = []
            for fuzzer in FUZZERS:
                if found[fuzzer] > 0 and facs_raw[fuzzer] == best_fac:
                    best_fuzzer.append(fuzzer)

            # make best fuzzer bold
            for fuzzer in best_fuzzer:
                latex = FUZZER_LATEX[fuzzer]
                rows[fuzzer] = rows[fuzzer].replace(latex, boldify(latex))

            # abbreviate Fuzzware
            rows["fuzzware"] = rows["fuzzware"].replace(r"\fuzzware", r"\fw")

            # collect rows
            first_row = True
            output_rows: List[str] = []
            for fuzzer in FUZZERS:
                # bug name
                if first_row:
                    first_row = False
                    row = r"    \multirow{3}{*}{" + \
                        bug_name_latex(bug) + r"} & "
                else:
                    row = f"    {' '*(17+len(bug))} & "

                # timings
                row += rows[fuzzer]

                # fac
                if fuzzer != baseline:
                    row += f" & {facs[fuzzer]}" + r" \\"
                else:
                    row += r" &             \\"

                output_rows.append(row)

            table += output_rows + [r"\midrule"]
    table = table[:-1] + [r"\arrayrulecolor{black}"]

    ## Use this to print table body to STDOUT
    # print("\n"*3)
    # print("\n".join(table))
    # print("\n"*3)

    print("## Average improvement factor")
    for fuzzer in FUZZERS:
        # comparing hoedur (baseline) against itself makes no sense
        if fuzzer == baseline:
            continue
        mean_fac = mean([t[fuzzer] for t in all_facs])
        median_fac = median([t[fuzzer] for t in all_facs])
        print(f"The average of factors (with which {baseline} found bugs faster than {fuzzer}) is {mean_fac} (median factor is {median_fac})")
    # print("\n"*3)

    return "\n".join(table)


def to_percentage(a: int, b: int) -> str:
    if b == 0:
        return "-"
    return f"{round(100 * a / b, 2)}%"


def found_in_one_day(timings: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Print how many runs hit the bug within the first 24h
    """
    total = sum([len(bugs) for bugs in timings.values()]) * NUM_RUNS
    found: Dict[str, int] = {}
    for fuzzer in FUZZERS:
        found[fuzzer] = 0

        for (target, bugs) in timings.items():
            for bug in bugs:
                (_, clean_data) = load_data(fuzzer, target, bug)
                target_found = 0
                for run in clean_data:
                    if run <= 24 * 3600:
                        target_found += 1
                found[fuzzer] += target_found

    print()
    print("## Number of runs that triggered bugs within the first 24 hours")
    print(
        f"Hoedur               triggered the bug in {found['hoedur']:2}/{total} runs ({to_percentage(found['hoedur'], total)})")
    print(
        f"Hoedur-single-stream triggered the bug in {found['hoedur-single-stream']:2}/{total} runs ({to_percentage(found['hoedur-single-stream'], total)})")
    print(
        f"Fuzzware             triggered the bug in {found['fuzzware']:2}/{total} runs ({to_percentage(found['fuzzware'], total)})")


def found_overall(timings: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Print how many runs hit the bug within the full runtime
    """
    total = sum([len(bugs) for bugs in timings.values()]) * NUM_RUNS
    found: Dict[str, int] = {}
    for fuzzer in FUZZERS:
        found[fuzzer] = 0

        for (target, bugs) in timings.items():
            for bug in bugs:
                (_, clean_data) = load_data(fuzzer, target, bug)
                target_found = 0
                for run in clean_data:
                    if run < 24 * 3600 * 15:
                        target_found += 1
                found[fuzzer] += target_found

    print()
    print("## Number of runs that triggered bugs during full runtime")
    print(
        f"Hoedur               triggered the bug in {found['hoedur']:2}/{total} runs ({to_percentage(found['hoedur'], total)})")
    print(
        f"Hoedur-single-stream triggered the bug in {found['hoedur-single-stream']:2}/{total} runs ({to_percentage(found['hoedur-single-stream'], total)})")
    print(
        f"Fuzzware             triggered the bug in {found['fuzzware']:2}/{total} runs ({to_percentage(found['fuzzware'], total)})")


def generate_table_one(timings_data: Dict[str, Dict[str, Dict[str, List[str]]]]) -> None:
    print("\n## TEX file")
    print(f"Writing Table 1 to {TABLE_ONE_PATH.as_posix()}\n")
    # Table 1
    exp_name = "fuzzware-cve"
    assert exp_name in timings_data, f"Expected timings data for 'fuzzware-cve' (Table 1) but key not found in config"
    timings = timings_data[exp_name]

    body = generate_table(timings)

    header = r"""\begin{table}[ht!]
    \caption{CVE discovery timings of known CVEs within 15 days. We round seconds to the closest minute and report the timings as \textbf{days:hours:minutes}. Based on the mean, we present the factor of how much faster a fuzzer is in \textbf{Fac.} (and mark the better fuzzer in bold). A fuzzer may fail to find the CVE within 15 days (see \textbf{\#Hit} column); in this case, we assume it triggers the CVE at 15 days and 1 second and represent these runs as ``---''. }%
    \label{tab:eval:cve_discovery_details}
    \centering
    \resizebox{\columnwidth}{!}{%
    \begin{tabular}{llcccccr}
    \toprule
    \multicolumn{1}{c}{\multirow{2}{*}{\textbf{CVE-20..}}} & \multicolumn{1}{c}{\multirow{2}{*}{\textbf{Fuzzer}}} & \multirow{2}{*}{\textbf{\#Hit}} & \multicolumn{1}{c}{\textbf{Min}} & \multicolumn{1}{c}{\textbf{Max}} & \multicolumn{1}{c}{\textbf{Median}} & \multicolumn{1}{c}{\textbf{Mean}} & \multicolumn{1}{c}{\multirow{2}{*}{\textbf{Fac.}}} \\
    & & & {\footnotesize dd:hh:mm} & {\footnotesize dd:hh:mm} & {\footnotesize dd:hh:mm} & {\footnotesize dd:hh:mm} & \\
    \midrule"""

    footer = r"""    \bottomrule
    \end{tabular}
    }
\end{table}
"""

    table = f"{header}\n{body}\n{footer}"

    # write table
    with open(TABLE_ONE_PATH, "w", encoding="utf-8") as f:
        f.write(table)

    # print some stats on how many runs hit the targets within 24h/full runtime
    found_in_one_day(timings)
    found_overall(timings)


def generate_table_two(timings_data: Dict[str, Dict[str, Dict[str, List[str]]]]) -> None:
    print("\n## TEX file")
    print(f"Writing Table 2 to {TABLE_TWO_PATH.as_posix()}\n")
    # Table 1
    exp_name = "new-bugs"
    assert exp_name in timings_data, f"Expected timings data for 'new-bugs' (Table 2) but key not found in config"
    timings = timings_data[exp_name]

    body = generate_table(timings)

    header = r"""\begin{table}[th]
    \caption{Timings of the discovery (within 15 days) of additional, previously unknown bugs in the Fuzzware target set. The format is equivalent to \tabref{tab:eval:cve_discovery_details}.}%
    \label{tab:eval:cve_discovery_details_new_CVEs}
    \centering
    \resizebox{\columnwidth}{!}{%
    \begin{tabular}{llcccccr}
    \toprule
    \multicolumn{1}{c}{\multirow{2}{*}{\textbf{CVE-20..}}} & \multicolumn{1}{c}{\multirow{2}{*}{\textbf{Fuzzer}}} & \multirow{2}{*}{\textbf{\#Hit}} & \multicolumn{1}{c}{\textbf{Min}} & \multicolumn{1}{c}{\textbf{Max}} & \multicolumn{1}{c}{\textbf{Median}} & \multicolumn{1}{c}{\textbf{Mean}} & \multicolumn{1}{c}{\multirow{2}{*}{\textbf{Fac.}}} \\
    & & & {\footnotesize dd:hh:mm} & {\footnotesize dd:hh:mm} & {\footnotesize dd:hh:mm} & {\footnotesize dd:hh:mm} & \\
    \midrule"""

    footer = r"""    \bottomrule
    \end{tabular}
    }
\end{table}
"""

    table = f"{header}\n{body}\n{footer}"

    with open(TABLE_TWO_PATH, "w", encoding="utf-8") as f:
        f.write(table)

    # print some stats on how many runs hit the targets within 24h/full runtime
    found_in_one_day(timings)
    found_overall(timings)


def main() -> None:
    # load timings data
    timings_data: Dict[str, Dict[str, Dict[str, List[str]]]] = EXPERIMENT["timings"] # type: ignore

    print("# Generating Table 1")
    generate_table_one(timings_data)
    print("\n"*2)

    print("="* 80 + "\n")
    print("# Generating Table 2")
    generate_table_two(timings_data)



if __name__ == "__main__":
    main()
