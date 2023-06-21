#!/usr/bin/env python3
import argparse
import importlib
import multiprocessing
import os

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))
REBUILT_DIR = DIR.parent.joinpath("rebuilt")
TARGETS = [entry.name for entry in os.scandir(DIR) if entry.is_dir()]

try:
    import docker
    from git import Repo, RemoteProgress
except ImportError as e:
    print(f"[ERROR] Could not import required libraries. Error: {e}")
    print(f"Please install the requirements via 'pip install -r {DIR}/requirements.txt'")
    exit(1)

class ProgressPrinter(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=""):
        print(
            op_code,
            cur_count,
            max_count,
            cur_count / (max_count or 100.0),
            message or "NO MESSAGE",
        )

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--targets", nargs="+", default=TARGETS, choices=TARGETS, help="Space separated list of targets, defaults to all")
    parser.add_argument("-s", "--subtargets", nargs="+", help="Space separated list of subtargets, defaults to all")
    return parser

def prepare_git(target_path, url, config):
    repo_path = target_path.joinpath("repo")
    if not repo_path.exists():
        repo_path.mkdir(exist_ok=True)
        print("Cloning repository:", url)
        repo = Repo.clone_from(url, repo_path, progress=ProgressPrinter())
    else:
        repo = Repo(repo_path)
    for submodule in repo.submodules:
        submodule.update(recursive=True, progress=ProgressPrinter())
    repo.head.reset(config["base_commit"], index=True, working_tree=True)
    repo.git.clean(force=True)
    for revert in config.get("revert_commits", []):
        repo.git.revert(revert, no_commit=True)
    for backport in config.get("backport_commits", []):
        repo.git.cherry_pick(backport, no_commit=True)
    for patch in config.get("patches", []):
        repo.git.apply(target_path.joinpath("patches", patch).absolute())
    return repo_path

def main():
    parser = create_parser()
    args = parser.parse_args()
    for target in args.targets:
        builder = importlib.import_module(target + ".build")
        target_config = builder.CONFIG

        # allow using the build function from another target but a different config
        if getattr(builder, "BUILD_OVERRIDE", None):
            builder = importlib.import_module(builder.BUILD_OVERRIDE + ".build")

        for subtarget, config in target_config.items():
            if args.subtargets and subtarget not in args.subtargets:
                continue
            target_path = DIR.joinpath(target)
            repo_path = prepare_git(target_path, builder.GIT_URL, config)
            cache_path = target_path.joinpath("cache")
            cache_path.mkdir(parents=True, exist_ok=True)
            out_path = REBUILT_DIR.joinpath(target, subtarget)
            out_path.mkdir(parents=True, exist_ok=True)
            builder.build(repo_path, out_path, cache_path, config, nproc=multiprocessing.cpu_count())


if __name__ == '__main__':
    main()
