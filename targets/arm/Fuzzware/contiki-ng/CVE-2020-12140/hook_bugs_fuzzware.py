# tcpip_ipv6_output+0x4e on_ipv6_routing_infinite_recursion_return
# tcpip_ipv6_output+0x4a on_ipv6_routing_infinite_recursion_enter
# rpl_ext_header_srh_update+0x10 on_rpl_ext_header_srh_update
# memcpy on_fraginfo_oob_writes
# memcpy on_packetbuf_oob_writes
# input+0xfa on_unchecked_sdu_length
# 0x00205b32 on_CVE_2020_12140_callsite_2
# 0x00205b10 on_CVE_2020_12140_callsite_1


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

# CVE check
L2CAP_BUFFER_LEN = 0x500

# Multiple Bugs require this
# PORTING: Symbol: packetbuf
PACKETBUF_ALIGNED = 0x200006b0
PACKETBUF_ALIGNED_LEN = 32 * 4

# Bug: fixed-Bug-invalid_SRH_address_pointer
# PORTING: Symbol: uip_aligned_buf
UIP_BUF = 0x200025c8
UIP_BUFSIZE = 1280

# Bug: new-Bug-ipv6_routing_infinite_recursion / stack_overflow
MAX_REC_DEPTH = 10

class Recursion:
    def __init__(self, depth=None):
        self.depth = depth


# Bug: new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write
# We hook memcpy calls with LRs known to originate from 6lo (checks relying on BLE_L2CAP_NODE_MTU) and l2cap (missing check)
# PORTING: memcpy call in function "output" (inlined compress_hdr_iphc) with variable size and related to the "hc06_ptr" variable
MEMCPY_CALL_LOC_COMPRESS_HDR_IPHC_PACKETBUF_OOB = 0x207AF0
# PORTING: memcpy call in function "output" (!frag_needed case) with variable size which is followed by function "send_packet"
MEMCPY_CALL_LOC_OUTPUT_PACKETBUF_OOB = 0x207C92
# PORTING: memcpy call in function "process_thread_ble_l2cap_tx_process" with variable size which is followed by packetbuf_set_datalen / ... / send
MEMCPY_CALL_LOC_BLE_L2CAP_TX_PROCESS = 0x205638
# PORTING: memcpy call in function "fragment_copy_payload_and_send". These OOBs (always) originate from output->fragment_copy_payload_and_send->memcpy
MEMCPY_CALL_LOC_fragment_copy_payload_and_send = 0x204bae
# PORTING: memcpy call in function "packetbuf_copyfrom". These OOBs (always) originate from output->fragment_copy_payload_and_send->queuebuf_to_packetbuf->packetbuf_copyfrom->memcpy
MEMCPY_CALL_LOC_packetbuf_copyfrom = 0x207512
# PORTING: memcpy call in function "compress_addr_64" (first call with constant size 2). These OOBs (always) originate from output->compress_addr_64->memcpy
MEMCPY_CALL_LOC_output_compress_addr_64_1 = 0x20748a
# PORTING: memcpy call in function "compress_addr_64" (second call with constant size 8). These OOBs (always) originate from output->compress_addr_64->memcpy
MEMCPY_CALL_LOC_output_compress_addr_64_2 = 0x20749e
# There are different, fixed/small-sized memcpy calls which may OOB in more niche situations create a catch-all here
# PORTING: sicslowpan_driver.output (mem.u32(symbols["sicslowpan_driver"]+0xc))
SICSLOWPAN_DRIVER_OUTPUT_FN = 0x207564
SICSLOWPAN_DRIVER_OUTPUT_FN_END = 0x207cb8

# memcpy packetbuf OOB cases
# PORTING: Hook return from memcpy call in input following packetbuf_dataptr (this matches the return for call hooked for unchecked_sdu_length)
MEMCPY_CALL_LOC_PACKETBUF_KNOWN_UNCHECKED_SDU = 0x205b7e
# PORTING: Hook return matching the first CVE_2020_12140 hook memcpy call in input
MEMCPY_CALL_LOC_PACKETBUF_KNOWN_CVE_2020_12140_1 = 0x205b28
# PORTING: Hook return matching the second CVE_2020_12140 hook memcpy call in input
MEMCPY_CALL_LOC_PACKETBUF_KNOWN_CVE_2020_12140_2 = 0x205b4a
# PORTING: Return from memcpy in input following assignment of packetbuf_payload_len and other OOB against IP packet length
# Fix: https://github.com/contiki-ng/contiki-ng/commit/c76aa9bc
MEMCPY_CALL_LOC_SICSLOWPAN_FIRSTFRAG_OR_UNFRAG_OOB = 0x208514
# PORTING: memcpy call in function "input" with variable size and related to the "hc06_ptr" variable
MEMCPY_CALL_LOC_UNCOMPRESS_HDR_IPHC = 0x208398

# Bugs: fixed-Bug-uncompress_hdr_iphc_oob_write
# PORTING: Symbol: frag_info
FRAG_INFO = 0x20000a10
# sicslowpan_frag_info frag_info[2]
FRAG_INFO_SIZE = 2 * 0xb8

#pub def main (api):
#    # CVE check
#    # Hook return from second memcpy in 3-time memcpy in function `input` (else case of `chan->rx_buffer.sdu_length`)
#    # Note that for fuzzware compatibility reasons, we cannot use the `input` symbol here (as there are two symbol definitions for `input`)
#    api.on_basic_block(Some(0x00205b10), |_| on_CVE_2020_12140_callsite_1())
#    # Hook return from first memcpy in 2-time memcpy in function `input` (if case of `chan->rx_buffer.sdu_length`)
#    # Note that for fuzzware compatibility reasons, we cannot use the `input` symbol here (as there are two symbol definitions for `input`)
#    api.on_basic_block(Some(0x00205b32), |_| on_CVE_2020_12140_callsite_2())
#
#    # Bug: new-Bug-unchecked_sdu_length
#    # PORTING: Hook return from packetbuf_dataptr before memcpy in `input_l2cap_frame_flow_channel` (inlined in function `input`)
#    api.on_basic_block(Some(globs.uc.symbols['input'] + 0xfa), |_| on_unchecked_sdu_length())
#
#    # Bug: new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write and fixed-Bug-uncompress_hdr_iphc_oob_write
#    api.on_basic_block(Some(globs.uc.symbols['memcpy']), |_| on_packetbuf_oob_writes())
#    # Bugs: fixed-Bug-fraginfo_oob_writes and fixed-Bug-6lo_firstfrag_oob_write
#    api.on_basic_block(Some(globs.uc.symbols['memcpy']), |_| on_fraginfo_oob_writes())
#
#    # Bugs: fixed-Bug-SRH_too_many_segments_left and fixed-Bug-invalid_SRH_address_pointer
#    # PORTING: Hook return from uipbuf_search_header in `rpl_ext_header_srh_update`
#    api.on_basic_block(Some(globs.uc.symbols['rpl_ext_header_srh_update'] + 0x10), |_| on_rpl_ext_header_srh_update())
#
#    # Bug: new-Bug-ipv6_routing_infinite_recursion / stack_overflow
#    recursion = Recursion: depth: 0 }
recursion = Recursion ( depth= 0 )
#    # PORTING: Hook tcpip_ipv6_output's call to packet_input
#    api.on_basic_block(Some(globs.uc.symbols['tcpip_ipv6_output'] + 0x4a), |_| on_ipv6_routing_infinite_recursion_enter(recursion))
#    # PORTING: Hook return of tcpip_ipv6_output's call of packet_input
#    api.on_basic_block(Some(globs.uc.symbols['tcpip_ipv6_output'] + 0x4e), |_| on_ipv6_routing_infinite_recursion_return(recursion))
#    # Reset depth for each input
#    #api.on_prepare_run(or: recursion.depth = 0 })
#}


# Count recursion depth for function packet_input (number of entries and exits)
def on_ipv6_routing_infinite_recursion_enter (uc):
    global recursion
    recursion.depth += 1
    if recursion.depth > MAX_REC_DEPTH:
        add_bug("new-Bug-ipv6_routing_infinite_recursion")

def on_ipv6_routing_infinite_recursion_return (uc):
    global recursion
    # Call exit
    recursion.depth -= 1

def on_rpl_ext_header_srh_update (uc):
    RPL_RH_LEN = 4
    RPL_SRH_LEN = 4

    rh_header = globs.uc.regs.r0
    # rh_header->len
    try:
        len = globs.uc.mem.u8(rh_header + 1)
    except UcError:
        return None
    ext_len = len * 8 + 8

    srh_header = rh_header + RPL_RH_LEN
    # rh_header->seg_left
    try:
        segments_left = globs.uc.mem.u8(rh_header + 3)
    except UcError:
        return None
    # srh_header->cmpr
    try:
        cmpr = globs.uc.mem.u8(srh_header + 0)
    except UcError:
        return None
    cmpri = cmpr >> 4
    cmpre = cmpr & 0x0f
    # srh_header->pad
    try:
        padding = globs.uc.mem.u8(srh_header + 1) >> 4
    except UcError:
        return None

    path_len = ((ext_len - padding - RPL_RH_LEN - RPL_SRH_LEN - (16 - cmpre)) / (16 - cmpri)) + 1

    # Fix: https://github.com/contiki-ng/contiki-ng/commit/f0bb7f314c424630837d2ed08ec0bc90e1ccb15e
    if segments_left > path_len:
        add_bug("fixed-Bug-SRH_too_many_segments_left")

    i = path_len - segments_left
    cmpr = 0
    if segments_left == 1:
        cmpr = cmpre
    else:
        cmpr = cmpri
    rh_offset = rh_header - UIP_BUF
    addr_offset = RPL_RH_LEN + RPL_SRH_LEN + (i * (16 - cmpri))

    # Fix: https://github.com/contiki-ng/contiki-ng/commit/99a9257421ca5305ef6a360c02f63561e63ecc60
    if rh_offset + addr_offset + 16 - cmpr > UIP_BUFSIZE:
        add_bug("fixed-Bug-invalid_SRH_address_pointer")

def on_unchecked_sdu_length (uc):
    packetbuf_dataptr = globs.uc.regs.r0
    channel = globs.uc.regs.r5
    # sdu_length = channel->rx_buffer.sdu_length
    try:
        sdu_length = globs.uc.mem.u16(channel + 0xa14)
    except UcError:
        return None

    # Fix: https://github.com/contiki-ng/contiki-ng/commit/506f9def7cdff853fa24cf6d88e1f4e5619dc46c
    if (packetbuf_dataptr + sdu_length) > (PACKETBUF_ALIGNED + PACKETBUF_ALIGNED_LEN):
        add_bug("new-Bug-unchecked_sdu_length")

def on_packetbuf_oob_writes (uc):
    dst = globs.uc.regs.r0

    # Check for any copies targeting packetbuf
    if (dst >= PACKETBUF_ALIGNED) and (dst < PACKETBUF_ALIGNED + PACKETBUF_ALIGNED_LEN):
        # Remaining buffer size: buffer len minus buffer cursor offset
        buf_size = PACKETBUF_ALIGNED_LEN - (dst - PACKETBUF_ALIGNED)
        n = globs.uc.regs.r2

        if n > buf_size:
            lr = globs.uc.regs.lr
            is_CVE_2020_12140 = lr == (MEMCPY_CALL_LOC_PACKETBUF_KNOWN_CVE_2020_12140_1 | 1) or lr == (MEMCPY_CALL_LOC_PACKETBUF_KNOWN_CVE_2020_12140_2 | 1)

            is_ble_l2cap_MTU_output_OOB = False
            # output OOB: Specific output call sites
            is_ble_l2cap_MTU_output_OOB = is_ble_l2cap_MTU_output_OOB or (lr == (MEMCPY_CALL_LOC_COMPRESS_HDR_IPHC_PACKETBUF_OOB | 1) or lr == (MEMCPY_CALL_LOC_OUTPUT_PACKETBUF_OOB | 1) or lr == (MEMCPY_CALL_LOC_BLE_L2CAP_TX_PROCESS | 1))
            # output OOB: Specific OOBs in (subcalls of) fragment_copy_payload_and_send resulting (directly) from 6lo output OOBs
            is_ble_l2cap_MTU_output_OOB = is_ble_l2cap_MTU_output_OOB or (lr == (MEMCPY_CALL_LOC_fragment_copy_payload_and_send | 1) or lr == (MEMCPY_CALL_LOC_packetbuf_copyfrom | 1))
            # output OOB: Specific OOBs in compress_addr_64 resulting (directly) from 6lo output OOBs
            is_ble_l2cap_MTU_output_OOB = is_ble_l2cap_MTU_output_OOB or (lr == (MEMCPY_CALL_LOC_output_compress_addr_64_1 | 1) or lr == (MEMCPY_CALL_LOC_output_compress_addr_64_2 | 1))
            # output OOB: Catch-all for Niche OOBs with small and constant-size memcpy calls originating
            is_ble_l2cap_MTU_output_OOB = is_ble_l2cap_MTU_output_OOB or ((lr >= SICSLOWPAN_DRIVER_OUTPUT_FN and lr < SICSLOWPAN_DRIVER_OUTPUT_FN_END) and (n > 0 and n < 0x20))

            if is_CVE_2020_12140 or lr == (MEMCPY_CALL_LOC_PACKETBUF_KNOWN_UNCHECKED_SDU | 1) or lr == (MEMCPY_CALL_LOC_SICSLOWPAN_FIRSTFRAG_OR_UNFRAG_OOB | 1):
                # ignore known packetbuf oob write sources from CVE_2020_12140, new-Bug-unchecked_sdu_length, fixed-Bug-6lo_firstfrag_oob_write
                return
            elif lr == (MEMCPY_CALL_LOC_UNCOMPRESS_HDR_IPHC | 1):
                # Fix commits:
                # uncompress_hdr_iphc retval: https://github.com/contiki-ng/contiki-ng/commit/971354a
                # uncompress_hdr_iphc bufsize arg: https://github.com/contiki-ng/contiki-ng/commit/b88e5c3
                # Main checks: https://github.com/contiki-ng/contiki-ng/commit/668f244
                # Off-by-one fix: https://github.com/contiki-ng/contiki-ng/commit/79cd1d6
                add_bug("fixed-Bug-uncompress_hdr_iphc_oob_write")
            elif is_ble_l2cap_MTU_output_OOB:
                # Fix: https://github.com/contiki-ng/contiki-ng/commit/6c71855
                add_bug("new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write")
            else:
                # Other LRs for memcpy OOBs into packet buffer
                add_bug("UNKNOWN-packetbuf_oob_write_{:08x}".format( lr))

def on_fraginfo_oob_writes (uc):
    dst = globs.uc.regs.r0

    # Check for any copies targeting fragment buffers
    if (dst >= FRAG_INFO) and (dst < FRAG_INFO + FRAG_INFO_SIZE):
        # Remaining buffer size: buffer len minus buffer cursor offset
        buf_size = FRAG_INFO_SIZE - (dst - FRAG_INFO)
        n = globs.uc.regs.r2

        if n > buf_size:
            lr = globs.uc.regs.lr

            if lr == (MEMCPY_CALL_LOC_UNCOMPRESS_HDR_IPHC | 1):
                # Fix commits:
                # uncompress_hdr_iphc retval: https://github.com/contiki-ng/contiki-ng/commit/971354a
                # uncompress_hdr_iphc bufsize arg: https://github.com/contiki-ng/contiki-ng/commit/b88e5c3
                # Main checks: https://github.com/contiki-ng/contiki-ng/commit/668f244
                # Off-by-one fix: https://github.com/contiki-ng/contiki-ng/commit/79cd1d6
                add_bug("fixed-Bug-uncompress_hdr_iphc_oob_write")
            elif lr == (MEMCPY_CALL_LOC_SICSLOWPAN_FIRSTFRAG_OR_UNFRAG_OOB | 1):
                # buffer_size tracking: https://github.com/contiki-ng/contiki-ng/commit/b88e5c3
                # buffer_size oob check: https://github.com/contiki-ng/contiki-ng/commit/c76aa9bc
                add_bug("fixed-Bug-6lo_firstfrag_oob_write")
            else:
                # Other LRs for memcpy OOBs into fragment buffers
                add_bug("UNKNOWN-fraginfo_oob_write_{:08x}".format( lr))

def check_packetbuf_oob (n):
    if n > L2CAP_BUFFER_LEN or n < 0:
        add_bug("CVE-2020-12140")

def on_CVE_2020_12140_callsite_1 (uc):
    sp = globs.uc.regs.sp
    try:
        len = globs.uc.mem.u16(sp + 4)
    except UcError:
        return None
    n = len - 2

    check_packetbuf_oob(n)

def on_CVE_2020_12140_callsite_2 (uc):
    sp = globs.uc.regs.sp
    try:
        len = globs.uc.mem.u16(sp + 4)
    except UcError:
        return None

    try:
        current_index = globs.uc.mem.u16(globs.uc.regs.r9 + 0xa16)
    except UcError:
        return None

    n = current_index + len

    check_packetbuf_oob(n)