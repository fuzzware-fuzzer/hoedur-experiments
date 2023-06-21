# memmove on_CVE_2021_3330


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

MEMMOVE_CALL_LOC_ieee802154_reassemble = 0x00403c7f

#pub def main (api):
#    # CVE check
#    api.on_basic_block(Some(globs.uc.symbols['memmove']), |_| on_CVE_2021_3330())
#}


def on_CVE_2021_3330 (uc):
    # Check for size underflow in memmove call from ieee802154_reassemble
    if globs.uc.regs.r2 > 0xf0000000 and globs.uc.regs.lr == MEMMOVE_CALL_LOC_ieee802154_reassemble:
        add_bug("CVE-2021-3330")