import docker
import os

from pathlib import Path

CONFIG = {
    "CVE-2022-39274": {
        "base_commit": "2ddd73feafd3316af2c547c34d6969bea637d5c6",
        "revert_commits": [],
        "patches": ["0001-simple-SPI-read.patch"],
        "target": "subsys/lorawan/class_a",
        "board": "lora_e5_dev_board",
    }
}
# uses the same build zephyr-os
BUILD_OVERRIDE = "zephyr-os"

