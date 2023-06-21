# net_buf_simple_add_mem on_CVE_2020_10065


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

ADD_MEM_CALL_LOC_spi_rx_thread = 0x8001355

#pub def main (api):
#    # CVE check
#    api.on_basic_block(Some(globs.uc.symbols['net_buf_simple_add_mem']), |_| on_CVE_2020_10065())
#}


def on_CVE_2020_10065 (uc):
    # Check for buf size OOB in calls to net_buf_simple_add_mem
    buf = globs.uc.regs.r0
    len = globs.uc.regs.r2
    try:
        buf_len = globs.uc.mem.u16(buf + 4)
    except UcError:
        return None
    try:
        buf_size = globs.uc.mem.u16(buf + 6)
    except UcError:
        return None

    if buf_len + len > buf_size:
        if globs.uc.regs.lr == ADD_MEM_CALL_LOC_spi_rx_thread:
            add_bug("CVE-2020-10065")
        else:
            add_bug("GENERIC-len-overflow")