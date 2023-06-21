import subprocess

# map CVE id to the fixing commit
FIX_COMMITS_MAPPING = {
    "CVE-2023-24817": {"4f1e2a370974da7796a9db3a0cbdb1556c134d4d"},
    "CVE-2023-24818": {
        "0bec3e245ed3815ad6c8cae54673f0021777768b",
        "17c70f7ee0b1445f2941f516f264ed4a096e82b7",
        "aa27ed71fa3e5d48dee1748dcf27b6323ec98a33",
    },
    "CVE-2023-24819": {"73615161c01fcfbbc7216cf502cabb12c1598ee4"},
    "CVE-2023-24820": {"2709fbd827b688fe62df2c77c316914f4a3a6d4a"},
    "CVE-2023-24821": {"9728f727e75d7d78dbfb5918e0de1b938b7b6d2c"},
    "CVE-2023-24822": {"639c04325de4ceb9d444955f4927bfae95843a39"},
    "CVE-2023-24823": {"4a081f86616cb5c9dd0b5d7b286da03285d1652a"},
    "CVE-2023-24825": {"709ddd2ba75dcc3cb0ed0e107f39a1bd9757c2a1"},
    # this fix commit doesn't apply cleanly, so we have to patch it manually
    "CVE-2023-24826": set(),  # {"eb9e50aafe300b75a30dc24e8c7005f88ecd5d1d"},
}

# set of all fix commits
FIX_COMMITS = set()
for commits in FIX_COMMITS_MAPPING.values():
    FIX_COMMITS.update(commits)

# additional fixes to apply
FIX_COMMITS.update({
    "b1dff296db8bff30caedf8db7a0d442ee6f0c922", # off-by-one in ethos driver
    "269b3c97c23ac14bfcacfb8d83a83501ffd277de", # off-by-one in slipdev driver
    })

BASE_CONFIG = {
    "base_commit": "2022.07",
    "target": "gnrc_networking",
    "release": "2022.07",
    "patches": [
        "base.patch",
        "increase_stack_size.patch",
        "gnrc_networking_activate_modules.patch",
        "remove_checksums.patch",
        "prevent_null_deref_gnrc_sixlowpan_frag_sfr_arq_timeout.patch",
        "fix_CVE-2023-24826.patch",
        "fix_CVE-2023-33973.patch",
        "fix_CVE-2023-33974.patch",
        "fix_CVE-2023-33975.patch",
    ],
}

# generate a config for each target where all bugs except one are fixed
CONFIG = {
    cve_id: {**BASE_CONFIG, "backport_commits": FIX_COMMITS.difference(commits)}
    for cve_id, commits in FIX_COMMITS_MAPPING.items()
}
CONFIG["CVE-2023-24826"]["patches"] = BASE_CONFIG["patches"].copy()
CONFIG["CVE-2023-24826"]["patches"].remove("fix_CVE-2023-24826.patch")

GIT_URL = "https://github.com/RIOT-OS/RIOT"


def build(repo_path, out_path, cache_path, config, nproc):
    env = {
        "BUILD_IN_DOCKER": "1",
        "DOCKER_IMAGE": f"riot/riotbuild:{config['release']}",
        "DOCKER_ENVIRONMENT_CMDLINE": "-e 'CFLAGS=-gdwarf-4 -gstrict-dwarf'",
    }
    target_path = repo_path.joinpath("examples", config["target"])
    subprocess.run(["make", "-C", target_path, "-j", str(nproc), "BOARD=cc2538dk", "clean", "all"], env=env, check=True)
    bin_path = target_path.joinpath("bin", "cc2538dk")
    bins = [f"{config['target']}.bin", f"{config['target']}.elf"]
    for bin in bins:
        bin_path.joinpath(bin).replace(out_path.joinpath(bin))
