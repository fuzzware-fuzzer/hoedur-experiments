#!/usr/bin/env python3
import argparse
import os
import subprocess

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))
CONTAINER_DIR = Path("/", "home", "user", "hoedur-experiments").absolute()
CONTAINER_TARGETS = CONTAINER_DIR.parent.joinpath('hoedur-targets')

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("bug_name", help="Name of the bug to run")
    parser.add_argument("--targets", type=Path, default=DIR.parent.parent.joinpath("targets"), help="Directory containing the target binaries")
    parser.add_argument("--results", type=Path, default=DIR.parent.joinpath("results", "bug-reproducers"), help="Directory containing the reproducers")
    parser.add_argument("--trace", default=False, action="store_true", help="Run the (slower), more detailed version which provides an additional run-time trace.")

    return parser

def run_hoedur_docker(cmd_args, targets, reproducer):
    docker_cmd_args = [
        "docker",
        "run",
        "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--mount", f"src={DIR.parent.parent},target=/home/user/hoedur-experiments,type=bind",
        "--mount", f"src={targets},target=/home/user/hoedur-targets,type=bind",
        "--mount", f"src={reproducer},target=/home/user/reproducer,type=bind",
        "-t",
        "hoedur-fuzzware"
    ]

    return subprocess.run(docker_cmd_args + cmd_args)

def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        reproducer = next(args.results.glob(f"**/new-Bug-{args.bug_name}")).absolute()
    except StopIteration:
        exit(f"No bug with name {args.bug_name} found")

    config = reproducer.joinpath("config.corpus.tar.zst").absolute()
    input = next(reproducer.glob("*.bin")).absolute()
    target = Path("arm", *reproducer.parts[-4:-1])
    cmd = [
        "python3",
        Path("04-prev-unknown-vulns", "scripts", "run_reproducer_docker.py"),
        target,
    ]
    if args.trace:
        cmd.append("--trace")

    run_hoedur_docker(cmd, args.targets, reproducer)

if __name__ == '__main__':
    main()
