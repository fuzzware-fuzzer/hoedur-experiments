# set_le_adv_enable_legacy.constprop.0+0x30 on_cmd_data_index
# bt_hci_cmd_send_sync+0x24 on_cmd_data_index
# bt_hci_cmd_create+0x32 on_cmd_data_index
# hci_cmd_done.isra.0+0x1e on_cmd_data_index
# bt_att_chan_req_send+0x28 on_bt_att_chan_req_send
# bt_conn_add_le+0x28 on_bt_conn_add_le_work_init
# conn_auto_initiate+0x106 on_conn_auto_initiate_call_work_submit
# bt_att_status+0x18 on_bt_att_status
# bt_att_recv+0xaa on_bt_att_recv
# bt_att_recv+0x74 on_bt_att_recv
# bt_att_recv+0x72 on_bt_att_recv
# bt_att_sent+0x18 on_bt_att_sent
# z_impl_k_queue_get+0xa4 on_k_queue_get_poll
# arch_swap+0x20 on_arch_swap_after_pendsv
# z_arm_pendsv on_z_arm_pendsv
# arch_swap on_arch_swap_enter
# hci_cmd_done.isra.0+0x32 on_hci_cmd_done_state_update
# set_le_adv_enable_legacy.constprop.0+0x30 on_set_le_adv_enable_legacy_send_sync
# hci_cmd_done.isra.0+0x62 on_bt_hci_cmd_done_check_sema_validity
# bt_hci_cmd_send_sync+0x78 on_bt_hci_cmd_send_sync_set_invalid
# bt_hci_cmd_send_sync+0x24 on_bt_hci_cmd_send_sync_set_valid
# net_buf_put on_net_buf_put_check_rx_tx_fifo_state
# bt_buf_get_cmd_complete+0x36 on_bt_buf_get_cmd_complete_sent_cmd_reuse
# net_buf_alloc_len+0xe6 on_net_buf_alloc_len_ret_check_nullptr_in_isr
# z_arm_int_exit on_isr_exit
# _isr_wrapper on_isr_entry
# z_impl_k_sem_take on_le_init_sem_take
# bt_init+0x2ae on_le_init_check_2
# bt_init+0x1ba on_le_init_check_1
# k_delayed_work_init on_k_delayed_work_init
# z_add_timeout on_z_add_timeout
# net_buf_simple_push on_net_buf_simple_push
# tx_free on_tx_free
# z_clock_announce+0x84 on_timeout_callback
# z_impl_k_sem_take on_z_impl_k_sem_take
# send_frag on_CVE_2021_3329
# bt_init+0x1e0 on_bt_init
# z_impl_k_sem_init on_semaphore_init


from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

class MtuSetup:
    def __init__(self, hit=None):
        self.hit = hit

class LeInit:
    def __init__(self, invalid_init=None):
        self.invalid_init = invalid_init

class IsrState:
    def __init__(self, depth=None):
        self.depth = depth

class SentCmdState:
    def __init__(self, bug=None, is_buf_handed_out_when_in_tx_fifo=None):
        self.bug = bug
        self.is_buf_handed_out_when_in_tx_fifo = is_buf_handed_out_when_in_tx_fifo

class SemaState:
    def __init__(self, valid=None, head=None, tail=None):
        self.valid = valid
        self.head = head
        self.tail = tail

class CmdData:
    def __init__(self, state=None, state_target=None):
        self.state = state
        self.state_target = state_target

class ArchSwap:
    def __init__(self, bug=None, pendsv=None):
        self.bug = bug
        self.pendsv = pendsv


#pub def main (api):
#    # CVE check
#    semaphores = []
semaphores = []
#    mtu_setup = MtuSetup { hit: False }
mtu_setup = MtuSetup ( hit= False )
#    #api.on_prepare_run(or { semaphores.clear() semaphores.append(0x20002f98) mtu_setup.hit = False })
#    api.on_basic_block(Some(globs.uc.symbols['z_impl_k_sem_init']), |_| on_semaphore_init(semaphores))
#    api.on_basic_block(Some(globs.uc.symbols['bt_init']+0x1e0), |_| on_bt_init(mtu_setup))
#    api.on_basic_block(Some(globs.uc.symbols['send_frag']), |_| on_CVE_2021_3329(semaphores, mtu_setup))
#    api.on_basic_block(Some(globs.uc.symbols['z_impl_k_sem_take']), |_| on_z_impl_k_sem_take(semaphores))
#    api.on_basic_block(Some(globs.uc.symbols['z_clock_announce']+0x84), |_| on_timeout_callback())
#    api.on_basic_block(Some(globs.uc.symbols['tx_free']), |_| on_tx_free())
#    api.on_basic_block(Some(globs.uc.symbols['net_buf_simple_push']), |_| on_net_buf_simple_push())
#    api.on_basic_block(Some(globs.uc.symbols['z_add_timeout']), |_| on_z_add_timeout())
#    api.on_basic_block(Some(globs.uc.symbols['k_delayed_work_init']), |_| on_k_delayed_work_init())
#
#    # PORTING: The basic block we are hooking here is in heavily inlined parts within bt_init -> hci_init -> le_init -> le_read_buffer_size_complete
#    # Specifically, we target the "bt_hci_cmd_send_sync(0x2002u, ...)", which is "bt_hci_cmd_send_sync(BT_HCI_OP_LE_READ_BUFFER_SIZE, ...)"
#    # location 1:
#    # https://github.com/zephyrproject-rtos/zephyr/blob/e1dddf7befa7309bd2afc567b2e00d2e7362f7c4/subsys/bluetooth/host/hci_core.c#L5576
#    # https://github.com/zephyrproject-rtos/zephyr/blob/e1dddf7befa7309bd2afc567b2e00d2e7362f7c4/subsys/bluetooth/host/hci_core.c#L5350-L5357
#    # location 2:
#    # https://github.com/zephyrproject-rtos/zephyr/blob/e1dddf7befa7309bd2afc567b2e00d2e7362f7c4/subsys/bluetooth/host/hci_core.c#L5784
#    # https://github.com/zephyrproject-rtos/zephyr/blob/e1dddf7befa7309bd2afc567b2e00d2e7362f7c4/subsys/bluetooth/host/hci_core.c#L5334-L5339
#    le_init = LeInit { invalid_init: False }
le_init = LeInit ( invalid_init= False )
#    #api.on_prepare_run(or { le_init.invalid_init = False })
#    api.on_basic_block(Some(globs.uc.symbols['bt_init']+0x1ba), |_| on_le_init_check_1(le_init))
#    api.on_basic_block(Some(globs.uc.symbols['bt_init']+0x2ae), |_| on_le_init_check_2(le_init))
#    api.on_basic_block(Some(globs.uc.symbols['z_impl_k_sem_take']), |_| on_le_init_sem_take(le_init))
#
#    # Bug: new-Bug-hci_prio_event_alloc_err_handling
#    isr_state = IsrState { depth: 0 }
isr_state = IsrState ( depth= 0 )
#    # PORTING: Ensure that upon start of a new run we are not within an ISR (depth = 0)
#    #api.on_prepare_run(or { isr_state.depth = 0 })
#    api.on_basic_block(Some(globs.uc.symbols['_isr_wrapper']), |_| on_isr_entry(isr_state))
#    api.on_basic_block(Some(globs.uc.symbols['z_arm_int_exit']), |_| on_isr_exit(isr_state))
#    # PORTING: Make sure that the return of net_buf_alloc_len is at the specified offset
#    api.on_basic_block(Some(globs.uc.symbols['net_buf_alloc_len'] + 0xe6), |_| on_net_buf_alloc_len_ret_check_nullptr_in_isr(isr_state))
#
#    # Bug: new-Bug-sent_cmd_shared_ref_race
#    # PORTING: Make sure that the sent_cmd re-use case of bt_buf_get_cmd_complete is at the correct offset
#    sent_cmd_state = SentCmdState { bug: False, is_buf_handed_out_when_in_tx_fifo: False }
sent_cmd_state = SentCmdState ( bug= False, is_buf_handed_out_when_in_tx_fifo= False )
#    #api.on_prepare_run(or { sent_cmd_state.bug = False sent_cmd_state.is_buf_handed_out_when_in_tx_fifo = False })
#    api.on_basic_block(Some(globs.uc.symbols['bt_buf_get_cmd_complete'] + 0x36), |_| on_bt_buf_get_cmd_complete_sent_cmd_reuse(sent_cmd_state))
#    api.on_basic_block(Some(globs.uc.symbols['net_buf_put']), |_| on_net_buf_put_check_rx_tx_fifo_state(sent_cmd_state))
#
#    # Bug: new-Bug-hci-send_sync-dangling-sema-ref
#    send_sync_sema_states = [SemaState { valid: False, head: 0, tail: 0}, SemaState { valid: False, head: 0, tail: 0}]
send_sync_sema_states = [SemaState ( valid= False, head= 0, tail= 0), SemaState ( valid= False, head= 0, tail= 0)]
#    #api.on_prepare_run(or { send_sync_sema_states[0].valid = False send_sync_sema_states[1].valid = False })
#    # PORTING: Offset: return from first call to net_buf_id within bt_hci_cmd_send_sync (pre z_impl_k_sem_take on sync_sem)
#    api.on_basic_block(Some(globs.uc.symbols['bt_hci_cmd_send_sync'] + 0x24), |_| on_bt_hci_cmd_send_sync_set_valid(send_sync_sema_states))
#    # PORTING: Offset: return from second call to net_buf_id within bt_hci_cmd_send_sync (post z_impl_k_sem_take on sync_sem)
#    api.on_basic_block(Some(globs.uc.symbols['bt_hci_cmd_send_sync'] + 0x78), |_| on_bt_hci_cmd_send_sync_set_invalid(send_sync_sema_states))
#    # PORTING: Offset: return from last net_buf_id call in hci_cmd_done before z_impl_k_sem_give is called on sync sema
#    api.on_basic_block(Some(globs.uc.symbols['hci_cmd_done.isra.0'] + 0x62), |_| on_bt_hci_cmd_done_check_sema_validity(send_sync_sema_states))
#
#    # Bug: new-Bug-hci-send_sync-dangling-conn-state-ref
#    cmd_data = [ CmdData { state: 0, state_target: 0 }, CmdData { state: 0, state_target: 0 } ]
cmd_data = [ CmdData ( state= 0, state_target= 0 ), CmdData ( state= 0, state_target= 0 ) ]
#    #api.on_prepare_run(or { cmd_data[0].state = 0 cmd_data[1].state = 0 })
#    # PORTING: Offset: Return from net_buf_id call just before bt_hci_cmd_send_sync
#    # PORTING: Function name may have changed in newer versions. See bt_hci_cmd_state_set_init calls before bt_hci_cmd_send_sync (bt_le_create_conn_legacy, ...)
#    api.on_basic_block(Some(globs.uc.symbols['set_le_adv_enable_legacy.constprop.0'] + 0x30), |_| on_set_le_adv_enable_legacy_send_sync(cmd_data))
#    # PORTING: Offset: Return from net_buf_id call just before atomic_set_bit_to
#    api.on_basic_block(Some(globs.uc.symbols['hci_cmd_done.isra.0'] + 0x32), |_| on_hci_cmd_done_state_update(cmd_data))
#
#    # Bug: fixed-Bug-k_poll-race-condition
#    # PORTING: z_impl_k_queue_get+a4 is just before `z_queue_node_peek´
#    # PORTING: arch_swap+20 is the basic block after `isb`
#    # NOTE: Ignore other known bugs also resulting in a nullptr.
#    #       The hook for `new-Bug-hci_prio_event_alloc_err_handling` triggers too late, use generic arch_swap not raising PendSV hook instead.
#    arch_swap = ArchSwap { bug: False, pendsv: False }
arch_swap = ArchSwap ( bug= False, pendsv= False )
#    #api.on_prepare_run(or { arch_swap.bug = False arch_swap.pendsv = False })
#    api.on_basic_block(Some(globs.uc.symbols['arch_swap']), |_| on_arch_swap_enter(arch_swap))
#    api.on_basic_block(Some(globs.uc.symbols['z_arm_pendsv']), |_| on_z_arm_pendsv(arch_swap))
#    api.on_basic_block(Some(globs.uc.symbols['arch_swap'] + 0x20), |_| on_arch_swap_after_pendsv(arch_swap))
#    api.on_basic_block(Some(globs.uc.symbols['z_impl_k_queue_get'] + 0xa4), |_| on_k_queue_get_poll(arch_swap, sent_cmd_state))
#
#    # Bug: fixed-Bug-bt_att-resp-timeout-null-ptr
#    # PORTING: Offset: In bt_att_sent after first NULL check
#    api.on_basic_block(Some(globs.uc.symbols['bt_att_sent'] + 0x18), |_| on_bt_att_sent())
#    # PORTING: Different BBs leading to calls of send_err_rsp or handlers
#    api.on_basic_block(Some(globs.uc.symbols['bt_att_recv'] + 0x72), |_| on_bt_att_recv()) # send_err_rsp (1)
#    api.on_basic_block(Some(globs.uc.symbols['bt_att_recv'] + 0x74), |_| on_bt_att_recv()) # send_err_rsp (2)
#    api.on_basic_block(Some(globs.uc.symbols['bt_att_recv'] + 0xaa), |_| on_bt_att_recv()) # handler->func
#    # PORTING: If CONFIG_BT_SMP is set, check for bt_att_encrypt_change call site (CONFIG_BT_SMP)
#    # https://github.com/zephyrproject-rtos/zephyr/commit/577cd82#diff-3adc165d775d407a3eb6b90da365671eee38ca4e38d9b6f6661abf2975a5161eR2703
#    # api.on_basic_block(Some(globs.uc.symbols['bt_att_encrypt_change'] + 0xTODO, on_bt_att_encrypt_change)
#    # PORTING: bt_att_status after initial checks before att is used
#    api.on_basic_block(Some(globs.uc.symbols['bt_att_status'] + 0x18), |_| on_bt_att_status())
#
#    # Bug: fixed-Bug-bt-periph-update_conn_param-work-double-submit
#    # PORTING: Offset: bb before calling k_delayed_work_submit_to_queue from conn_auto_initiate
#    api.on_basic_block(Some(globs.uc.symbols['conn_auto_initiate'] + 0x106), |_| on_conn_auto_initiate_call_work_submit())
#    # PORTING: Offset: bb before calling k_delayed_work_init from bt_conn_add_le
#    api.on_basic_block(Some(globs.uc.symbols['bt_conn_add_le'] + 0x28), |_| on_bt_conn_add_le_work_init())
#
#    # Bug: fixed-Bug-double-bt_att_chan_req_send-null-ptr
#    # https://github.com/zephyrproject-rtos/zephyr/commit/bc7ce86ac5c234a92cfc6302452a9aa962ff4952
#    api.on_basic_block(Some(globs.uc.symbols['bt_att_chan_req_send'] + 0x28), |_| on_bt_att_chan_req_send())
#
#    # Bug: GENERIC-cmd_data-oob-index
#    api.on_basic_block(Some(globs.uc.symbols['hci_cmd_done.isra.0'] + 0x1e), |_| on_cmd_data_index())
#    api.on_basic_block(Some(globs.uc.symbols['bt_hci_cmd_create'] + 0x32), |_| on_cmd_data_index())
#    api.on_basic_block(Some(globs.uc.symbols['bt_hci_cmd_send_sync'] + 0x24), |_| on_cmd_data_index())
#    api.on_basic_block(Some(globs.uc.symbols['set_le_adv_enable_legacy.constprop.0'] + 0x30), |_| on_cmd_data_index())
#}


def on_bt_init (uc):
    global mtu_setup
    mtu_setup.hit = True

def on_semaphore_init (uc):
    global semaphores
    sem = globs.uc.regs.r0
    semaphores.append(sem)

    # detect invalid semaphore init
    initial_count = globs.uc.regs.r1
    limit = globs.uc.regs.r2
    if limit == 0 or initial_count > limit:
        print("invalid z_impl_k_sem_init call: sem = {:08x}, initial_count = {}, limit = {}".format( sem, initial_count, limit))
        add_bug("GENERIC-invalid-sem-init-{:08x}".format( sem))

def on_CVE_2021_3329 (uc):
    global semaphores
    global mtu_setup
    # semaphore init done?
    sem = 0x20002f7c
    init = False
    for addr in semaphores:
        if addr == sem:
            init = True
            break

    # CVE-2021-3329
    if mtu_setup.hit and not init:
        add_bug("CVE-2021-3329")

def on_z_impl_k_sem_take (uc):
    global semaphores
    sem = globs.uc.regs.r0

    # semaphore init done?
    init = False
    for addr in semaphores:
        if addr == sem:
            init = True
            break

    # use sempahore before init?
    if not init:
        add_bug("GENERIC-sem-not-init-{:08x}".format( sem))

def on_isr_entry (uc):
    global isr_state
    isr_state.depth += 1

def on_isr_exit (uc):
    global isr_state
    isr_state.depth -= 1

def on_net_buf_alloc_len_ret_check_nullptr_in_isr (uc):
    global isr_state
    # Check whether NULL is returned from blocking netbuf allocation when within an ISR
    if isr_state.depth > 0:
        # PORTING: ensure r4 holds the return value
        buf = globs.uc.regs.r4
        # PORTING: ensure r6 holds timeout
        timeout = globs.uc.regs.r6

        # The bug triggers when NULL is returned from blocking net_buf_alloc while in an ISR
        K_FOREVER = 0xffffffff
        if timeout == K_FOREVER and buf == 0:
            add_bug("new-Bug-hci_prio_event_alloc_err_handling")

# Parse fifo list at `fifo_addr` and check whether buffer `buf` is part of it
def fifo_contains (fifo_addr, buf):
    next = fifo_addr
    nodes = []

    while next != 0:
        # detect loops
        for node in nodes:
            if node == next:
                return False
        nodes.append(next)

        # buf found in fifo
        if next == buf:
            return True

        # resolve next list node
        # PYTHON: address may be unmapped and reading it will return an error, replace error with 0
        try:
            next = globs.uc.mem.u32(next)
        except UcError:
            next = 0

    # end of list
    return False

def on_bt_buf_get_cmd_complete_sent_cmd_reuse (uc):
    global sent_cmd_state
    # Check whether sent_cmd is re-used while it is still in the output queue (tx.fifo)

    tx_fifo = globs.uc.symbols['tx'] + 0x8 # tx.fifo (addr: 0x20003038)

    # PORTING: register assignment (r4 == sent_cmd)
    sent_cmd_netbuf = globs.uc.regs.r4

    if fifo_contains(tx_fifo, sent_cmd_netbuf):
        sent_cmd_state.is_buf_handed_out_when_in_tx_fifo = True

def on_net_buf_put_check_rx_tx_fifo_state (uc):
    global sent_cmd_state
    # After the sent_cmd has been given out, is a buffer also added to rx.fifo while it is in tx.fifo?

    if sent_cmd_state.is_buf_handed_out_when_in_tx_fifo:
        rx_fifo = globs.uc.symbols['rx'] + 4 # rx.fifo (addr: 0x20003014)
        tx_fifo = globs.uc.symbols['tx'] + 8 # tx.fifo (addr: 0x20003038)
        target_queue = globs.uc.regs.r0

        if target_queue == rx_fifo:
            buf_to_add = globs.uc.regs.r1

            if fifo_contains(tx_fifo, buf_to_add):
                add_bug("new-Bug-sent_cmd_shared_ref_race")
                sent_cmd_state.bug = True

def on_bt_hci_cmd_send_sync_set_valid (uc):
    global send_sync_sema_states
    # After sync_sem is set up in bt_hci_cmd_send_sync and while z_impl_k_sem_take is called on it, sema may be used

    net_buf_id = globs.uc.regs.r0
    sema = globs.uc.regs.sp

    if net_buf_id == 0 or net_buf_id == 1:
        send_sync_sema_states[net_buf_id].valid = True
        try:
            send_sync_sema_states[net_buf_id].head = globs.uc.mem.u32(sema)
        except UcError:
            return None
        try:
            send_sync_sema_states[net_buf_id].tail = globs.uc.mem.u32(sema+4)
        except UcError:
            return None

def on_bt_hci_cmd_send_sync_set_invalid (uc):
    global send_sync_sema_states
    # After z_impl_k_sem_take has returned within bt_hci_cmd_send_sync, sema is no longer valid

    net_buf_id = globs.uc.regs.r0

    if net_buf_id == 0 or net_buf_id == 1:
        send_sync_sema_states[net_buf_id].valid = False

def on_bt_hci_cmd_done_check_sema_validity (uc):
    global send_sync_sema_states
    # Check whether sync sema on command buffer is valid in case it is about to be used
    # PORTING: symbol cmd_data_0 + 8
    GLOBAL_cmd_data_0_sync = 0x20000294 + 8
    CMD_DATA_SIZE = 0xc
    net_buf_id = globs.uc.regs.r0

    if net_buf_id == 0 or net_buf_id == 1:
        if not send_sync_sema_states[net_buf_id].valid:
            sema_ptr_addr = GLOBAL_cmd_data_0_sync + net_buf_id * CMD_DATA_SIZE
            try:
                sema_addr = globs.uc.mem.u32(sema_ptr_addr)
            except UcError:
                return None

            # This in itself should not happen, but does not lead to an actual crash most of the time
            # This is why we check here whether the sema waitq addresses remained unchanged
            try:
                head = globs.uc.mem.u32(sema_addr)
            except UcError:
                return None
            try:
                tail = globs.uc.mem.u32(sema_addr+4)
            except UcError:
                return None
            if send_sync_sema_states[net_buf_id].head != head or \
                send_sync_sema_states[net_buf_id].tail != tail:
                    add_bug("new-Bug-hci-send_sync-dangling-sema-ref")

def on_arch_swap_enter (uc):
    global arch_swap
    arch_swap.pendsv = False

def on_z_arm_pendsv (uc):
    global arch_swap
    arch_swap.pendsv = True

def on_arch_swap_after_pendsv (uc):
    global arch_swap
    if not arch_swap.pendsv:
        arch_swap.bug = True

# https://github.com/zephyrproject-rtos/zephyr/commit/99c2d2d0
# https://github.com/zephyrproject-rtos/zephyr/commit/b173e4353fe55c42ee7f77277e13106021ba5678
def on_k_queue_get_poll (uc):
    global arch_swap
    global sent_cmd_state
    other_bug = arch_swap.bug or sent_cmd_state.bug
    node = globs.uc.regs.r0

    # k_poll is racy and peeking is not atomic
    # queue head may be a nullptr by the time of use and the code **should** retry but does not => bug
    # NOTE: ignore known Bug(s) where arch_swap fails to raise an PendSV interrupt
    if node == 0 and not other_bug:
        add_bug("fixed-Bug-k_poll-race-condition")

def on_le_init_check_1 (uc):
    global le_init
    # PORTING: Need to ensure that the rsp (response) variable is located at sp+0x4 here
    rsp_ptr_ptr = globs.uc.regs.sp + 4
    try:
        buf = globs.uc.mem.u32(rsp_ptr_ptr)
    except UcError:
        return None

    # PORTING: Make sure that struct formats remain the same
    try:
        data = globs.uc.mem.u32(buf + 8)
    except UcError:
        return None

    # Offsets into struct bt_hci_rp_le_read_buffer_size (https://github.com/zephyrproject-rtos/zephyr/blob/e1dddf7befa7309bd2afc567b2e00d2e7362f7c4/include/bluetooth/hci.h#L600-L604)
    # rp->le_max_len
    try:
        le_max_len = globs.uc.mem.u16(data + 1)
    except UcError:
        return None
    # rp->le_max_num
    try:
        le_max_num = globs.uc.mem.u8(data + 3)
    except UcError:
        return None

    # Bug: if le_max_len is set, le_max_num is also expected to be non-zero (but check is missing)
    # for le_max_num == 0, the semaphore initialization is invalid
    if le_max_len != 0 and le_max_num == 0:
        le_init.invalid_init = True

def on_le_init_check_2 (uc):
    global le_init
    # PORTING: Need to ensure that the rsp (response) variable is located at sp+0x4 here
    rsp_ptr_ptr = globs.uc.regs.sp + 4
    try:
        buf = globs.uc.mem.u32(rsp_ptr_ptr)
    except UcError:
        return None

    # PORTING: Make sure that struct formats remain the same
    try:
        data = globs.uc.mem.u32(buf + 8)
    except UcError:
        return None

    # Offsets into struct bt_hci_rp_read_buffer_size (https://github.com/zephyrproject-rtos/zephyr/blob/e1dddf7befa7309bd2afc567b2e00d2e7362f7c4/include/bluetooth/hci.h#L555-L561)
    # rp->acl_max_len
    try:
        acl_max_num = globs.uc.mem.u16(data + 4)
    except UcError:
        return None

    if acl_max_num == 0:
        le_init.invalid_init = True

def on_le_init_sem_take (uc):
    global le_init
    # PORTING: &_data_ram_start.le.pkts == 0x20002F7C
    LE_INIT_SEM = 0x20002F7C

    # detect bug on actual usage of semaphore
    sem = globs.uc.regs.r0
    if sem == LE_INIT_SEM and le_init.invalid_init:
        add_bug("new-Bug-invalid-init-le_read_buffer_size")

def on_timeout_callback (uc):
    t = globs.uc.regs.r0
    try:
        callback = globs.uc.mem.u32(t + 0xc)
    except UcError:
        return None

    if callback == 0:
        add_bug("GENERIC-invalid_timeout_callback")

# https://github.com/zephyrproject-rtos/zephyr/commit/577cd82#diff-3adc165d775d407a3eb6b90da365671eee38ca4e38d9b6f6661abf2975a5161eR287
def on_bt_att_sent (uc):
    # PORTING: r6 == att
    att = globs.uc.regs.r6

    if att == 0:
        add_bug("fixed-Bug-bt_att-resp-timeout-null-ptr")

# https://github.com/zephyrproject-rtos/zephyr/commit/577cd82#diff-3adc165d775d407a3eb6b90da365671eee38ca4e38d9b6f6661abf2975a5161eR2441
def on_bt_att_recv (uc):
    # PORTING: r6 == att_chan
    att_chan = globs.uc.regs.r6
    try:
        att = globs.uc.mem.u32(att_chan) # att_chan->att
    except UcError:
        return None

    if att == 0:
        add_bug("fixed-Bug-bt_att-resp-timeout-null-ptr")

# https://github.com/zephyrproject-rtos/zephyr/commit/577cd82#diff-3adc165d775d407a3eb6b90da365671eee38ca4e38d9b6f6661abf2975a5161eR2752
def on_bt_att_status (uc):
    # PORTING: r0 == ch
    ch = globs.uc.regs.r0
    att_chan = ch - 4                 # ATT_CHAN(ch)
    try:
        att = globs.uc.mem.u32(att_chan) # att_chan->att
    except UcError:
        return None

    if att == 0:
        add_bug("fixed-Bug-bt_att-resp-timeout-null-ptr")

# https://github.com/zephyrproject-rtos/zephyr/commit/77b11d6
# The fix is implicit in the fact that submitting work is now guarded by conn state machine in bt_conn_set_state
def on_conn_auto_initiate_call_work_submit (uc):
    # Check in conn_auto_initiate before submitting work that it is not already linked/added
    # This is the first known order in which the work timeout on connections may be used while already inserted

    # PORTING: struct offsets and r4==conn
    STRU_OFF_conn_to_update_work = 0x50
    STRU_OFF_work_to_timeout = 0xc
    conn = globs.uc.regs.r4
    update_work = conn + STRU_OFF_conn_to_update_work
    timeout = update_work + STRU_OFF_work_to_timeout

    timeout_list = globs.uc.symbols['timeout_list']
    if fifo_contains(timeout_list, timeout):
        add_bug("fixed-Bug-bt-periph-update_conn_param-work-double-submit")

def on_bt_conn_add_le_work_init (uc):
    # Check in bt_conn_add_le before initializing work that it is not already linked/added.
    # This is the second known order in which the work timeout on connections may be used while already inserted

    # PORTING: struct offsets and r4==conn
    STRU_OFF_conn_to_update_work = 0x50
    STRU_OFF_work_to_timeout = 0xc
    conn = globs.uc.regs.r4
    update_work = conn + STRU_OFF_conn_to_update_work
    timeout = update_work + STRU_OFF_work_to_timeout

    timeout_list = globs.uc.symbols['timeout_list']
    if fifo_contains(timeout_list, timeout):
        add_bug("fixed-Bug-bt-periph-update_conn_param-work-double-submit")

def on_k_delayed_work_init (uc):
    work = globs.uc.regs.r0
    STRU_OFF_work_to_timeout = 0xc
    timeout = work + STRU_OFF_work_to_timeout

    timeout_list = globs.uc.symbols['timeout_list']
    if fifo_contains(timeout_list, timeout):
        add_bug("GENERIC-delayed_work_init-double-add")

    # __ASSERT(!sys_dnode_is_linked(&to->node), "") in z_add_timeout
    try:
        next = globs.uc.mem.u32(timeout)
    except UcError:
        return None
    if next != 0:
        add_bug("GENERIC-delayed_work_init-sys_dnode_is_linked")

def on_z_add_timeout (uc):
    to = globs.uc.regs.r0

    timeout_list = globs.uc.symbols['timeout_list']
    if fifo_contains(timeout_list, to):
        add_bug("GENERIC-add_timeout-double-add")

    # __ASSERT(!sys_dnode_is_linked(&to->node), "") in z_add_timeout
    try:
        next = globs.uc.mem.u32(to)
    except UcError:
        return None
    if next != 0:
        add_bug("GENERIC-add_timeout-sys_dnode_is_linked")

def on_tx_free (uc):
    tx = globs.uc.regs.r0

    if tx & 0xff == 0x02:
        # NOTE: user_data buffer is reused in `send_frag` for `bt_send`
        # buf->user_data[0] = '\x02'
        # but `buf->user_data` is also a `tx` pointer
        # this error probably occurs due to a race condition / unexpected IRQ
        add_bug("GENERIC-invalid-tx_free")    

def on_set_le_adv_enable_legacy_send_sync (uc):
    global cmd_data
    # Save our local variable pointer when passing it to bt_hci_cmd_send_sync
    index = globs.uc.regs.r0
    state = globs.uc.regs.sp + 4
    try:
        target = globs.uc.mem.u32(state)
    except UcError:
        return None

    if index >= 2:
        # OOB index for cmd_data, this is the result of another bug
        # we detect this condition with the GENERIC-cmd_data-oob-index hook
        return

    cmd_data[index].state = state
    cmd_data[index].state_target = target

def on_hci_cmd_done_state_update (uc):
    global cmd_data
    # When state pointer is used in hci_cmd_done, check that its state->target has not been modified

    index = globs.uc.regs.r0
    if index >= 2:
        # OOB index for cmd_data, this is the result of another bug
        # we detect this condition with the GENERIC-cmd_data-oob-index hook
        return

    # PORTING: symbol cmd_data_0 + 4
    GLOBAL_cmd_data_0_state = 0x20000294 + 4
    CMD_DATA_SIZE = 0xc
    cmd_data_ptr = GLOBAL_cmd_data_0_state + (CMD_DATA_SIZE * index)
    try:
        state = globs.uc.mem.u32(cmd_data_ptr)
    except UcError:
        return None

    if state != 0:
        try:
            target = globs.uc.mem.u32(state)
        except UcError:
            return None

        # verify the state pointer to a value in the stack in set_le_adv_enable_legacy is still valid
        if target != cmd_data[index].state_target:
            add_bug("new-Bug-hci-send_sync-dangling-conn-state-ref")

def on_bt_att_chan_req_send (uc):
    # Porting: req==r4, bt_att_req->buf offset
    req = globs.uc.regs.r4
    try:
        buf = globs.uc.mem.u32(req + 0x10)
    except UcError:
        return None

    if buf == 0:
        add_bug("fixed-Bug-double-bt_att_chan_req_send-null-ptr")

def on_cmd_data_index (uc):
    index = globs.uc.regs.r0
    if index >= 2:
        add_bug("GENERIC-cmd_data-oob-index")

#size_t net_buf_simple_headroom(struct net_buf_simple *buf)
#{
#	return buf->data - buf->__buf
#}
def net_buf_simple_headroom (buf):
    if buf == 0:
        return 0

    try:
        buf_data = globs.uc.mem.u32(buf)
    except UcError:
        return None
    try:
        buf___buf = globs.uc.mem.u32(buf+8)
    except UcError:
        return None

    return buf_data - buf___buf

def on_net_buf_simple_push (uc):
    # __ASSERT_NO_MSG(net_buf_simple_headroom(buf) >= len)
    buf = globs.uc.regs.r0
    len = globs.uc.regs.r1

    if net_buf_simple_headroom(buf) < len:
        lr = globs.uc.regs.lr
        add_bug("GENERIC-net_buf_simple_push-underflow-{:08x}".format( lr))
