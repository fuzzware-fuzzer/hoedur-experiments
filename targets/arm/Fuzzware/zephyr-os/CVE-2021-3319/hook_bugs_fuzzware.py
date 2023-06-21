# 0x0040d41c on_CVE_2021_3319
# 0x0040d420 on_CVE_2021_3319
# 0x0040d390 on_CVE_2021_3319
# 0x0040d318 on_CVE_2021_3319


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

class Addr:
    def __init__(self, ptr=None):
        self.ptr = ptr


#pub def main (api):
#    # CVE check
#    mhr_src_addr = Addr { ptr: False }
mhr_src_addr = Addr ( ptr= False )
#    #api.on_prepare_run(or { mhr_src_addr.ptr = False })
#    # Hook different places in ieee802154_validate_frame (see comments below)
#    api.on_basic_block(Some(0x0040d318), |pc| on_CVE_2021_3319(pc, mhr_src_addr))
#    api.on_basic_block(Some(0x0040d390), |pc| on_CVE_2021_3319(pc, mhr_src_addr))
#    api.on_basic_block(Some(0x0040d420), |pc| on_CVE_2021_3319(pc, mhr_src_addr))
#    api.on_basic_block(Some(0x0040d41c), |pc| on_CVE_2021_3319(pc, mhr_src_addr))
#}


def on_CVE_2021_3319 (uc):
    pc = uc.regs.pc
    global mhr_src_addr
    # Catch NULL return from validate_addr outside IEEE802154_ADDR_MODE_NONE
    # https://github.com/zephyrproject-rtos/zephyr/blob/0aaae4a039cab54df84c1f0371d44d6045ff58d8/subsys/net/l2/ieee802154/ieee802154_frame.c#L120

    # validate_addr is inlined in ieee802154_validate_frame for source and destination addresses
    # This is why we catch both cases (src and dest NULL assignment)
    # Source Address is combined as 0x0040d420 is reachable via multiple paths
    if pc == 0x0040d318:
        # Reset tracking of whether we have a pointer when entering ieee802154_validate_frame
        mhr_src_addr.ptr = False
    elif pc == 0x0040d390:
        # We are in the "is a pointer" path
        mhr_src_addr.ptr = True
    elif pc == 0x0040d420:
        # Source address pointer assignment path triggered
        if mhr_src_addr.ptr:
            add_bug("CVE-2021-3319")
    elif pc == 0x0040d41c:
        # Destination address (NULL assignment only reached in buggy case)
        add_bug("CVE-2021-3319")