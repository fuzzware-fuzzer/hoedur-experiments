# snmp_message_decode on_snmp_message_decode_args_generic
# snmp_oid_copy+0x16 on_snmp_oid_copy_write
# snmp_engine_get_bulk on_snmp_engine_get_bulk
# snmp_oid_decode_oid+0x60 on_snmp_oid_decode_oid_oob
# snmp_message_decode+0x9e on_snmp_message_decode_check_bounds
# snmp_message_decode+0x92 on_snmp_message_decode_update_buf_len
# snmp_message_decode on_snmp_message_decode_args


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

OID_END = 0x20000c10
PACKET_LEN_PTR = 0x20000bcc
PACKET_LEN = 512

class SnmpArgs:
    def __init__(self, buf=None, buf_len=None):
        self.buf = buf
        self.buf_len = buf_len


#pub def main (api):
#    # CVE check
#    args = SnmpArgs { buf: 0, buf_len: 0 }
args = SnmpArgs ( buf= 0, buf_len= 0 )
#    api.on_basic_block(Some(globs.uc.symbols['snmp_message_decode']), |_| on_snmp_message_decode_args(args))
#    # PORTING: hook before snmp_ber_decode_string => update last buf_len
#    api.on_basic_block(Some(globs.uc.symbols['snmp_message_decode']+0x92), |_| on_snmp_message_decode_update_buf_len(args))
#    # PORTING: after snmp_ber_decode_string
#    api.on_basic_block(Some(globs.uc.symbols['snmp_message_decode']+0x9e), |_| on_snmp_message_decode_check_bounds(args))
#
#    # Bug: fixed-Bug-snmp_oid_decode_oid_oob
#    # PORTING: Hook bb after zero check in decoding loop of snmp_oid_decode_oid
#    api.on_basic_block(Some(globs.uc.symbols['snmp_oid_decode_oid']+0x60), |_| on_snmp_oid_decode_oid_oob())
#
#    # Bug: fixed-Bug-snmp_engine_get_bulk-varbinds_length-oob
#    api.on_basic_block(Some(globs.uc.symbols['snmp_engine_get_bulk']), |_| on_snmp_engine_get_bulk())
#
#    # Bug: fixed-Bug-snmp_oid_copy-missing-terminator-oob
#    # Porting: Hook after 0xffffffff termination check is passed and next write about to occur
#    api.on_basic_block(Some(globs.uc.symbols['snmp_oid_copy']+0x16), |_| on_snmp_oid_copy_write())
#
#    # Catch-all hooks: There are different, non-distinct places in snmp handling where similar out-of-bounds accesses may be performed
#    # As the SNMP implementation was replaced completely, we assume the non-distinct crashes to be collisions with CVE-2020-12141
#    args_generic = SnmpArgs { buf: 0, buf_len: 0 }
args_generic = SnmpArgs ( buf= 0, buf_len= 0 )
#    api.on_basic_block(Some(globs.uc.symbols['snmp_message_decode']), |_| on_snmp_message_decode_args_generic(args_generic))
#    api.on_basic_block(None, |pc| on_snmp_message_decode_check_bounds_generic(pc, args_generic))
#    api.on_basic_block(None, |_| packet_oob())
#}


# We duplicate this function for compatibility with fuzzware hook conversion
def on_snmp_message_decode_args (uc):
    global args
    args.buf = globs.uc.regs.r0
    args.buf_len = globs.uc.regs.r1

def on_snmp_message_decode_args_generic (uc):
    global args_generic
    args_generic.buf = globs.uc.regs.r0
    args_generic.buf_len = globs.uc.regs.r1

def on_snmp_message_decode_update_buf_len (uc):
    global args
    sp = globs.uc.regs.sp
    try:
        buf_len = globs.uc.mem.u32(sp + 4)
    except UcError:
        return None

    args.buf_len = buf_len

def on_snmp_message_decode_check_bounds (uc):
    global args
    sp = globs.uc.regs.sp
    try:
        buf_len = globs.uc.mem.u32(sp + 4)
    except UcError:
        return None

    # buf_len overflow
    if buf_len > args.buf_len:
        add_bug("CVE-2020-12141")

def on_snmp_message_decode_check_bounds_generic (uc):
    pc = uc.regs.pc
    global args_generic
    # only validate in snmp_message_decode
    if pc < 0x002058c2 or pc > 0x00205bb4:
        return

    sp = globs.uc.regs.sp
    try:
        buf_len = globs.uc.mem.u32(sp + 4)
    except UcError:
        return None

    # verify buf_len never increases
    if buf_len > args_generic.buf_len:
        # NOTE: this is a more generic check for OOB's in CVE-2020-12141
        add_bug("DUPLICATE-CVE-2020-12141")

    # update last buf_len
    args_generic.buf_len = buf_len

def packet_oob ():
    try:
        packet_len = globs.uc.mem.u32(PACKET_LEN_PTR)
    except UcError:
        return None

    if packet_len > PACKET_LEN:
        # NOTE: this is a more generic check for OOB's in CVE-2020-12141
        add_bug("DUPLICATE-CVE-2020-12141")

def on_snmp_oid_decode_oid_oob (uc):
    r2 = globs.uc.regs.r2

    if r2 > OID_END:
        add_bug("fixed-Bug-snmp_oid_decode_oid_oob")

def on_snmp_engine_get_bulk (uc):
    varbinds_length_ptr = globs.uc.regs.r2
    try:
        varbinds_length = globs.uc.mem.u32(varbinds_length_ptr)
    except UcError:
        return None

    if varbinds_length > 2:
        add_bug("fixed-Bug-snmp_engine_get_bulk-varbinds_length-oob")

def on_snmp_oid_copy_write (uc):
    # Before writing in snmp_oid_copy, check that the index is in bounds of 16 u32's

    # Porting: r2 == i
    OID_ARR_SIZE = 16
    write_ind = globs.uc.regs.r2

    if write_ind >= OID_ARR_SIZE:
        add_bug("fixed-Bug-snmp_oid_copy-missing-terminator-oob")
