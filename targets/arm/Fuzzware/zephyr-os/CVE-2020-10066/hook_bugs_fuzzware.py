# hci_cmd_done.isra.0 on_CVE_2020_10066


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

#pub def main (api):
#    # CVE check
#    api.on_basic_block(Some(globs.uc.symbols['hci_cmd_done.isra.0']), |_| on_CVE_2020_10066())
#}


def on_CVE_2020_10066 (uc):
    # Check for NULL netbuf pointer being passed to hci_cmd_done
    if globs.uc.regs.r1 == 0:
        add_bug("CVE-2020-10066")