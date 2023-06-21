# ieee802154_recv+0x42 on_CVE_2021_3320


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

IEEE802154_FRAME_TYPE_ACK = 2

#pub def main (api):
#    # CVE check
#    # Hook handling of incoming frames after initial sanity checks in ieee802154_recv
#    api.on_basic_block(Some(globs.uc.symbols['ieee802154_recv'] + 0x42), |_| on_CVE_2021_3320())
#}


def on_CVE_2021_3320 (uc):
    # Check for unexpected frame type
    if globs.uc.regs.r3 == IEEE802154_FRAME_TYPE_ACK:
        add_bug("CVE-2021-3320")