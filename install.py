#!/usr/bin/env python3

import argparse
import os
import subprocess
from urllib.error import ContentTooShortError, HTTPError
from urllib.request import urlretrieve

from pathlib import Path

DIR = Path(os.path.dirname(os.path.realpath(__file__)))

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prebuilt", default=False, action="store_true", help="Import pre-built docker containers instead of rebuilding them.")
    return parser

def import_docker_containers():
    # Verfiy docker images are available
    PACKED_IMAGE_NAMES = [
        ('fuzzware', 'https://pixeldrain.com/api/file/KthTbreF?download'),
        ('hoedur-fuzzware', 'https://pixeldrain.com/api/file/55EMUd8t?download'),
        ('hoedur-plotting-env', 'https://pixeldrain.com/api/file/SstNd4xb?download'),
    ]
    for (docker, download_url) in PACKED_IMAGE_NAMES:
        filename = f'{docker}.docker.tar.zst'
        path = DIR / 'install' / filename

        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            print(f'[*] Docker image {docker} is not available in {path}. Downloading from {download_url}...')
            try:
                urlretrieve(download_url, path)
            except ContentTooShortError as e:
                print(f'[ERROR] Download interrupted. Error: {e}.')
                exit(1)
            except HTTPError as e:
                print(f'[ERROR] Got Error while downloading: {e}.')
                exit(2)

            if not path.is_file():
                print(f'[ERROR] Could not download {download_url}.')
                exit(3)

    # Import docker images
    subprocess.check_call([DIR / "scripts" / "import_docker.sh"])

    print(f"[WARNING] You are using the pre-built docker images, which may have issues on your hardware. Please try to build your own docker images by running `./install.py` if you experience any issues.")

def rebuild_docker_containers():
    # Fuzzware docker container
    subprocess.check_call([DIR.joinpath("scripts", "fuzzware", "build_fuzzware_docker.sh")])

    # Hoedur docker container
    subprocess.check_call([DIR.joinpath("scripts", "hoedur", "build_docker.sh")])

    # Eval Data Processing docker container
    subprocess.check_call(["make", "-C", DIR.joinpath("scripts", "eval_data_processing"), "docker-image"])

def check_install():
    # Run install check script
    subprocess.check_call([DIR / "scripts" / "check_install.py"])

def main():
    parser = create_parser()
    args = parser.parse_args()

    is_prebuilt = args.prebuilt

    if is_prebuilt:
        import_docker_containers()
    else:
        rebuild_docker_containers()

    try:
        check_install()
    except subprocess.CalledProcessError as err:
        print(f"[ERROR] Installation ran to completion, but install check failed.\nError: {err}")

if __name__ == "__main__":
    main()
