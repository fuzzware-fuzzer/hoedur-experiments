# net_if_ipv6_calc_reachable_time on_net_if_ipv6_calc_reachable_time
# net_if_config_ipv6_get on_net_if_config_ipv6_get
# ieee802154_reassemble+0x246 on_fragment_remove_headers
# net_6lo_uncompress on_CVE_2021_3322
# ieee802154_recv+0x42 on_CVE_2021_3320
# memmove on_CVE_2020_10064


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

IEEE802154_FRAME_TYPE_ACK = 2
MEMMOVE_CALL_LOC_net_6lo_uncompress = 0x00407987

#pub def main (api):
#    # CVE check
#    api.on_basic_block(Some(globs.uc.symbols['memmove']), |_| on_CVE_2020_10064())
#    # Other CVEs triggerable in this target
#    # Hook handling of incoming frames after initial sanity checks in ieee802154_recv
#    api.on_basic_block(Some(globs.uc.symbols['ieee802154_recv'] + 0x42), |_| on_CVE_2021_3320())
#    api.on_basic_block(Some(globs.uc.symbols['net_6lo_uncompress']), |_| on_CVE_2021_3322())
#    # Bug: fixed-Bug-fragment_header_len
#    # Hook (inlined) handling of fragment_remove_headers in ieee802154_reassemble
#    api.on_basic_block(Some(globs.uc.symbols['ieee802154_reassemble'] + 0x246), |_| on_fragment_remove_headers())
#    # Bug: fixed-Bug-ipv6_get-iface-nullptr
#    api.on_basic_block(Some(globs.uc.symbols['net_if_config_ipv6_get']), |_| on_net_if_config_ipv6_get())
#    # Bug: new-Bug-ipv6-nullptr
#    api.on_basic_block(Some(globs.uc.symbols['net_if_ipv6_calc_reachable_time']), |_| on_net_if_ipv6_calc_reachable_time())
#}


def on_CVE_2020_10064 (uc):
    # Check for size underflow in memmove call from net_6lo_uncompress
    if globs.uc.regs.r2 > 0xf0000000 and globs.uc.regs.lr == MEMMOVE_CALL_LOC_net_6lo_uncompress:
        add_bug("CVE-2020-10064")

def on_CVE_2021_3320 (uc):
    if globs.uc.regs.r3 == IEEE802154_FRAME_TYPE_ACK:
        add_bug("COLLISION-CVE-2021-3320")

def on_CVE_2021_3322 (uc):
    # Check for NULL ptr in pkt->frags
    pkt = globs.uc.regs.r0
    try:
        frags = globs.uc.mem.u32(pkt + 0x10)
    except UcError:
        return None

    if frags == 0:
        add_bug("COLLISION-CVE-2021-3322")

# https://github.com/zephyrproject-rtos/zephyr/commit/d4b9620
# https://github.com/zephyrproject-rtos/zephyr/commit/897698b
def on_net_if_config_ipv6_get (uc):
    iface = globs.uc.regs.r0

    if iface == 0:
        add_bug("fixed-Bug-ipv6_get-iface-nullptr")

# https://github.com/zephyrproject-rtos/zephyr/commit/c6c2098
def on_net_if_ipv6_calc_reachable_time (uc):
    # PORTING: net_if_ipv6_calc_reachable_time is called two times, but once with an address of a global variable.
    #          Thus, NULL can only be passed from handle_ra_input. Make sure no other calls were added.

    # net_pkt_iface(pkt)->config.ip.ipv6
    ipv6 = globs.uc.regs.r0

    if ipv6 == 0:
        add_bug("new-Bug-ipv6-nullptr")

# https://github.com/zephyrproject-rtos/zephyr/commit/6068079
def on_fragment_remove_headers (uc):
    # 00404826  a868       ldr     r0, [r5, #8]
    # 00404828  aa89       ldrh    r2, [r5, #0xc]
    # 0040482c  03f0f803   and     r3, r3, #0xf8
    # 00404830  c02b       cmp     r3, #0xc0

    ptr = globs.uc.regs.r5
    try:
        buf_len = globs.uc.mem.u16(ptr + 0xc)
    except UcError:
        return None
    try:
        datagram_type = globs.uc.mem.u8(ptr + 8)
    except UcError:
        return None
    hdr_len = 0

    if datagram_type & 0xf8 == 0xc0:
        hdr_len = 4
    else:
        hdr_len = 5

    if buf_len < hdr_len:
        add_bug("fixed-Bug-fragment_header_len")
