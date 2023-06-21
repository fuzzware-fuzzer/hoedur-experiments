# net_6lo_uncompress+0x46 on_CVE_2021_3323_callsite_2
# net_6lo_uncompress+0x3e on_CVE_2021_3323_callsite_1


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

#pub def main (api):
#    # CVE check
#    # PORTING: hook bbs leading to call to net_buf_simple_tailroom in net_6lo_uncompress
#    api.on_basic_block(Some(globs.uc.symbols['net_6lo_uncompress'] + 0x3e), |_| on_CVE_2021_3323_callsite_1())
#    api.on_basic_block(Some(globs.uc.symbols['net_6lo_uncompress'] + 0x46), |_| on_CVE_2021_3323_callsite_2())
#}


def check_compressed_hdr_size (compressed_hdr_size):
    net_buf = globs.uc.regs.r6
    pkt_buf_len_addr = (net_buf + 0x8) + 0x4
    try:
        pkt_buf_len = globs.uc.mem.u16(pkt_buf_len_addr)
    except UcError:
        return None

    if pkt_buf_len < compressed_hdr_size:
        add_bug("CVE-2021-3323")

def on_CVE_2021_3323_callsite_1 (uc):
    compressed_hdr_size = globs.uc.regs.r3

    check_compressed_hdr_size(compressed_hdr_size)

def on_CVE_2021_3323_callsite_2 (uc):
    compressed_hdr_size = globs.uc.regs.r4

    check_compressed_hdr_size(compressed_hdr_size)