#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))
HOME = DIR.parent.parent.parent

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help="Target path to replay bug trigger crash in.")
    parser.add_argument("--trace", default=False, action="store_true", help="Run the (slower), more detailed version which provides an additional run-time trace.")

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    do_trace = args.trace
    target = args.target

    reproducer = HOME.joinpath("reproducer")
    config = reproducer.joinpath("config.corpus.tar.zst")
    input = next(reproducer.glob("input-*.bin"))

    target = HOME.joinpath("hoedur-targets", target)
    hook = target.joinpath("hook-bugs.rn")
    aux_hook = DIR.joinpath("hook-crash.rn")
    if do_trace:
        aux_hook = DIR.joinpath("hook-trace.rn")

    cmd = [
        "hoedur-arm",
        "--debug",
        "--trace",
        "--hook", hook,
        "--hook", aux_hook,
        "--import-config", config,
        "run",
        input,
    ]
    subprocess.run(cmd)

if __name__ == '__main__':
    main()


