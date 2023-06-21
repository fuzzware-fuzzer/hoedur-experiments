import docker
import os

from pathlib import Path

CONFIG = {
    "CVE-2022-3806": {
        "base_commit": "4256cd41df6c60f1832fd2deb14edc30ac7debab",
        "patches": [
            "bluetooth_hci_overlay.patch",
            "bt_hci_cmd_timeout.patch",
            "bt_hostonly_build.patch",
            "stm32f4_cap_flash_region_sizes.patch",
            "arm_generic_atomic.patch",
        ],
        "target": "bluetooth/peripheral_dis",
        "board": "nucleo_f429zi",
        "shield": "x_nucleo_idb05a1",
        "overlays": "bluetooth_hci.conf",
    },
}

GIT_URL = "https://github.com/zephyrproject-rtos/zephyr"
DOCKER_IMAGE = "zephyrprojectrtos/ci:v0.26.4"
WORKDIR = Path("/workdir")
CONTAINER_REPO = WORKDIR.joinpath("zephyr")


def build(repo_path, out_path, cache_path, config, nproc):
    build_path = CONTAINER_REPO.joinpath("samples", config["target"])
    client = docker.from_env()

    build_args = []
    if config.get("shield"):
        build_args.append("SHIELD=" + config["shield"])
    if config.get("overlays"):
        build_args.append("OVERLAY_CONFIG=" + config["overlays"])
    build_args.extend(config.get("extra_defines", []))
    build_args = " ".join(["-D" + arg for arg in build_args])

    cmd = "bash -c 'west update;"
    cmd += f"west build --pristine always -b {config['board']} {build_path} -- {build_args}'"
    volumes = [
        f"{cache_path}:{WORKDIR}",
        f"{repo_path}:{CONTAINER_REPO}",
    ]
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

    bin_path = cache_path.joinpath("build", "zephyr")
    bins = ["zephyr.elf", "zephyr.bin"]
    for bin in bins:
        bin_path.joinpath(bin).replace(out_path.joinpath(bin))
