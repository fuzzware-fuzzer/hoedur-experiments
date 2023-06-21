# net_6lo_uncompress on_CVE_2021_3322


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

#pub def main (api):
#    # CVE check
#    api.on_basic_block(Some(globs.uc.symbols['net_6lo_uncompress']), |_| on_CVE_2021_3322())
#}


def on_CVE_2021_3322 (uc):
    # Check for NULL ptr in pkt->frags
    pkt = globs.uc.regs.r0
    try:
        frags = globs.uc.mem.u32(pkt + 0x10)
    except UcError:
        return None

    if frags == 0:
        add_bug("CVE-2021-3322")