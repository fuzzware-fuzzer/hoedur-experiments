import docker
import os

from pathlib import Path

CONFIG = {
    "CVE-2023-31129": {
        "base_commit": "9771e9aaebbfbb5633ce69eb9876e0fc70bbcd6f",
        "patches": [
            "cc2538_norom.patch",
            "cc2538_read.patch",
            "enc28j60_read.patch",
            "transparent_mac.patch",
            "ip64_sample.patch",
            "link_address_granularity.patch",
            "ipv6_checksums.patch",
            "0001-ip64-dns64-add-bounds-checks-in-ip64_dns64_6to4.patch",
            "0002-ip64-dns64-add-bounds-checks-in-ip64_dns64_4to6.patch",
        ],
        "example": "ip64-router",
        "target": "zoul",
    },
    "CVE-2022-41873": {
        "base_commit": "9771e9aaebbfbb5633ce69eb9876e0fc70bbcd6f",
        "backport_commits": [
            "e871d479962d747465a7d8d58c5352212a4e6e0d", # CVE-2022-41972
            "6c71855d734a1034160e4bec6c5ad469cd62fbba", # CVE-2023-28116
            "20ae1a06f2fa13acfba43da73adb71dc61fcef84", # CVE-2023-23609
        ],
        "patches": [
            "cc2538_norom.patch",
            "cc2538_read.patch",
            "l2cap_sample.patch",
        ],
        "example": "hello-world",
        "target": "cc2538dk",
    },
    "CVE-2022-41972": {
        "base_commit": "9771e9aaebbfbb5633ce69eb9876e0fc70bbcd6f",
        "backport_commits": [
            "f28ca563e3882d4719d56f3bcd50a4e74edfa0ea", # CVE-2022-41873
            "6c71855d734a1034160e4bec6c5ad469cd62fbba", # CVE-2023-28116
            "20ae1a06f2fa13acfba43da73adb71dc61fcef84", # CVE-2023-23609
        ],
        "patches": [
            "cc2538_norom.patch",
            "cc2538_read.patch",
            "l2cap_sample.patch",
        ],
        "example": "hello-world",
        "target": "cc2538dk",
    },
}

GIT_URL = "https://github.com/contiki-ng/contiki-ng"
DOCKER_IMAGE = "contiker/contiki-ng:f823e6a1"
WORKDIR = Path("/workdir")


def build(repo_path, out_path, cache_path, config, nproc):
    example = config["example"]
    build_path = WORKDIR.joinpath("examples", example)
    client = docker.from_env()
    target = config.get("target", "cc2538dk")
    cmd = f"make -C {build_path} TARGET={target} distclean all"
    volumes = [f"{repo_path}:{WORKDIR}"]
    container = client.containers.run(
        DOCKER_IMAGE,
        cmd,
        detach=True,
        remove=True,
        user=os.getuid(),
        volumes=volumes,
        working_dir=str(WORKDIR),
    )
    for line in container.logs(stream=True):
        print(line.decode(), end="")

    if target == "zoul":
        bin_path = repo_path.joinpath("examples", example, "build", target, "orion")
    else:
        bin_path = repo_path.joinpath("examples", example, "build", target)
    bins = [f"{example}.elf", f"{example}.bin"]
    for bin in bins:
        bin_path.joinpath(bin).replace(out_path.joinpath(bin))
