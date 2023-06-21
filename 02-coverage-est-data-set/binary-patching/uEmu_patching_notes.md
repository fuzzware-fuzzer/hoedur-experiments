# Patching uEmu Targets

## utasker_USB

### Bug 1: OOB Write in USB Buffers

#### Bug Description
Affected function:
```
void __fastcall fnExtractFIFO(volatile unsigned int *ptrRxFIFO, USB_HW *ptr_usb_hardware, int iEndpoint_ref) {
  int usLength usLength = ptr_usb_hardware->usLength;
  unsigned int *buf = ptr_usb_hardware->ulUSB_buffer[iEndpoint_ref];
  // ...
    while ( usLength >= 1 )
  {
    *buf++ = *ptrRxFIFO;
    usLength -= 4;
  }
}
```

The issue here is that `ulUSB_buffer` is a two-dimensional buffer with 16 endpoints, which each hold 4 dwords (16 bytes)
worth of buffer data (`ulUSB_buffer    DCD 64`). This leaves a valid max buffer length (`usLength`) of 16.

The endpoint reference is masked by 0xf (`iEndpoint_ref`), limiting the size to 16 entries. However, `usLength` is not
restricted this way. Any value larger than 16 will overflow the buffer.

#### Fix
Fix description: restrict the length that may reach the function.

Patching idea:
- Restrict size on assignment of `usLength` in function `USB_OTG_FS_Interrupt`
- Do this by reducing the number of bytes extracted / the bit mask applied to input

Patch locations (pre patch):
```
2. Write location 1: usb_hardware.usLength = (v0 >> 4) & 0x7FF;
P1_ro:0800DAF6 CA F3 0A 10                 UBFX.W  R0, R10, #4, #0xB ; Unsigned Bit Field Extract
P1_ro:0800DAFA 08 80                       STRH    R0, [R1]        ; Store to Memory

1. Write location 2: usb_hardware.usLength = (MEMORY[0x50000020] >> 4) & 0x7FF;
P1_ro:0800DBC6 CA F3 0A 10                 UBFX.W  R0, R10, #4, #0xB ; Unsigned Bit Field Extract
P1_ro:0800DBCA 08 80                       STRH    R0, [R1]        ; Store to Memory
```
Patch mechanic:
- Restrict `usLength` by modifying the bitmask from `0x7FF` to `0xF`.
- This will allow a maximum of 16 bytes to be written to each USB buffer.

Patch locations (post patch)
```
1. Write location 2: usb_hardware.usLength = (unsigned __int8)v0 >> 4;
P1_ro:0800DAF6 CA F3 03 10                 UBFX.W  R0, R10, #4, #4 ; Unsigned Bit Field Extract
P1_ro:0800DAFA 08 80                       STRH    R0, [R1]        ; Store to Memory

2. Write location 1: usb_hardware.usLength = MEMORY[0x50000020] >> 4;
P1_ro:0800DBC6 CA F3 03 10                 UBFX.W  R0, R10, #4, #4 ; Unsigned Bit Field Extract
P1_ro:0800DBCA 08 80                       STRH    R0, [R1]        ; Store to Memory
```

Binary patches:
```
usLength_assignment_1:
    description: "Reduce maximum buffer size for size assignment 1"
    address: 0x0800DAF8
    binfile_offset: 0x1a78
    patch_contents: "03"
usLength_assignment_2:
    description: "Reduce maximum buffer size for size assignment 2"
    address: 0x0800DBC8
    binfile_offset: 0x1b48
    patch_contents: "03"
```

### Bug 2: Endpoint Index Out-of-Bounds
When processing USB input, the endpoint reference index is not checked against the number of allocated USB endpoints.

#### Bug Description
When the USB device is initially opened in the Bluetooth process' setup function, two USB endpoints are allocated. However, a total of 16 endpoints are supported by
the USB device. Consequently, input processing in function `fnEndpointData` uses the allocated buffer referenced by global variable `usb_endpoint_control` without
checking the number of initialized endpoints, which can lead to an out-of-bounds read on the heap.

Rather than a real bug, this bug likely occurs as hardware assumptions are violated. However, it may lead to out-of-bounds data to be de-referenced as a function pointer,
and my thus affect coverage measurements by introducing invalid coverage.


#### Fix
Fix description: When read from MMIO input, restrict the USB endpoint index to the known-to-be-initialized range of USB devices (2).

Patching idea:
- Restrict the USB index to 0-1
- Achieve this by modifying the bit extraction opcode from `v & 0xf` to `v & 0x1`

Patch locations (pre patch):
```
P1_ro:0800DABC 1A F0 0F 04                 ANDS.W  R4, R10, #0xF
P1_ro:0800DAC0 0A F4 F0 10                 AND.W   R0, R10, #0x1E0000
P1_ro:0800DAC4 7B D1                       BNE     loc_800DBBE
```

Patch locations (post patch):
```
P1_ro:0800DABC 1A F0 01 04                 ANDS.W  R4, R10, #0x1
P1_ro:0800DAC0 0A F4 F0 10                 AND.W   R0, R10, #0x1E0000
P1_ro:0800DAC4 7B D1                       BNE     loc_800DBBE
```

Binary patches:
```
endpoint_index_assignment:
    description: "Restrict the maximum USB reference index to 0-1 (as only 2 endpoints are allocated, not the maximum 16 supported by the driver logic)"
    address: 0x800dabe
    binfile_offset: 0x1a3e
    patch_contents: "01"
```

### Bug 3: Endpoint Index Out-of-Bounds

#### Bug Description
When processing USB setup data of type `SET_LINE_CODING`, the interface index is not explicitly checked against the expected index `0` in function `fnNewUART_settings` (which is inlined in `control_callback` in the given sample). This results in a `<=7` bytes write into an attacker-controlled offset into the global `uart_setting` array (which is allocated as of size 1).

Vulnerable source code: https://github.com/uTasker/uTasker-Kinetis/blob/39a40a91115937d248c5f587a36c2bf699fd870e/Applications/uTaskerV1.4/usb_application.c#L1938

#### Fix
Fix description: Make sure the index does not point out-of-bounds of the array. In this case, this means enforcing an index of `0` due to array size 1.

Patching idea:
- NOP out every addition to the base destination pointer that gets initialized to the address of the global `uart_setting` variable.

Patch locations (pre patch):
```
P1_ro:08011C28 CA EB CA 00                 RSB.W   R0, R10, R10,LSL#3
P1_ro:08011C2C 48 44                       ADD     R0, ptrData
P1_ro:08011C2E 5B 42                       NEGS    R3, R3
P1_ro:08011C30 18 44                       ADD     R0, R3
P1_ro:08011C32 5A 46                       MOV     R2, R11         ; Size
P1_ro:08011C34 31 46                       MOV     R1, R6          ; ptrFrom
P1_ro:08011C36 C0 1D                       ADDS    R0, R0, #7      ; ptrTo
P1_ro:08011C38 FD F7 94 FD                 BL      uMemcpy
```

Patch locations (post patch):
```
P1_ro:08011C28 4F F0 00 00                 MOV.W   R0, #0
P1_ro:08011C2C 48 44                       ADD     R0, ptrData
P1_ro:08011C2E 5B 42                       NEGS    R3, R3
P1_ro:08011C30 00 BF                       NOP
P1_ro:08011C32 5A 46                       MOV     R2, R11         ; Size
P1_ro:08011C34 31 46                       MOV     R1, R6          ; ptrFrom
P1_ro:08011C36 00 BF                       NOP
P1_ro:08011C38 FD F7 94 FD                 BL      uMemcpy
```

Binary patches:
```
uart_settings_interface_index:
    description: "Restrict the maximum index to 0 by removing all increments over uart_setting"
    address: 0x8011C28
    binfile_offset: 0x5ba8
    patch_contents: "4FF0000048445B4200BF5A46314600BF"
```

### Bug 4: Race Condition in TTY Initialization

#### Bug Description
When initializing the debug serial interface via `fnSetNewSerialMode`, `fnApplication` does not set the `0x4` flag of `ucDriverMode`. This missing flag encodes the assumption that `fnApplication`
is the first place from which the `fnSetNewSerialMode` function is called.

However, the same function `fnSetNewSerialMode` is also called from different other places, such as the USB task (`fnTaskUSB`). These other functions call `fnSetNewSerialMode` with `ucDriverMode==0x4==MODIFY_CONFIG`, indicating no read or write access (`FOR_READ==1` or `FOR_WRITE==2`). In case these functions call `fnSetNewSerialMode` first, the queue read/write
buffers will be left uninitialized.

#### Fix
Fix description: Remove racing calls to `fnSetNewSerialMode`.

Patching idea:
- NOP (racy) out calls to `fnSetNewSerialMode` which set `ucDriverMode==0x4`.

Patch locations (pre patch):
```
P1_ro:0801198C 00 20                       MOVS    R0, #0          ; ptrInterfaceParameters
P1_ro:0801198E 04 21                       MOVS    R1, #4          ; ucDriverMode
P1_ro:08011990 00 F0 38 FD                 BL      fnSetNewSerialMode

P1_ro:08012E96 04 21                       MOVS    R1, #4          ; ucDriverMode
P1_ro:08012E98 00 20                       MOVS    R0, #0          ; ptrInterfaceParameters
P1_ro:08012E9A FF F7 B3 FA                 BL      fnSetNewSerialMode

P1_ro:080137C4 04 21                       MOVS    R1, #4
P1_ro:080137C6 00 20                       MOVS    R0, #0
P1_ro:080137C8 FE F7 1C BE                 B.W     fnSetNewSerialMode
```

Patch locations (post patch):
```
P1_ro:0801198C 00 20                       MOVS    R0, #0          ; ptrInterfaceParameters
P1_ro:0801198E 04 21                       MOVS    R1, #4          ; ucDriverMode
P1_ro:08011990 00 BF                       NOP
P1_ro:08011992 00 BF                       NOP

P1_ro:08012E96 04 21                       MOVS    R1, #4          ; ucDriverMode
P1_ro:08012E98 00 20                       MOVS    R0, #0          ; ptrInterfaceParameters
P1_ro:08012E9A 00 BF                       NOP
P1_ro:08012E9C 00 BF                       NOP

P1_ro:080137C4 04 21                       MOVS    R1, #4
P1_ro:080137C6 00 20                       MOVS    R0, #0
P1_ro:080137C8 00 BF                       NOP
P1_ro:080137CA 00 BF                       NOP
```

Binary patches:
```
uart_fnSetNewSerialMode_race_call_1:
    description: "Remove mode 4 call to fnSetNewSerialMode"
    address: 0x8011990
    binfile_offset: 0x5910
    patch_contents: "00bf00bf"
uart_fnSetNewSerialMode_race_call_2:
    description: "Remove mode 4 call to fnSetNewSerialMode"
    address: 0x8012E9A
    binfile_offset: 0x6e1a
    patch_contents: "00bf00bf"
uart_fnSetNewSerialMode_race_call_3:
    description: "Remove mode 4 call to fnSetNewSerialMode"
    address: 0x80137C8
    binfile_offset: 0x7748
    patch_contents: "00bf00bf"
```

### Bug 5: OOB Array Access on SerialHandle_0
Also see the same Bug in utasker_MODBUS

#### Bug Description
The issue occurs while processing MODBUS frame inputs in function `fnMODBUS`. The function performs a bounds check on the incoming target serial handle index, but checks against a too large bounds. The check is performed for the value <=10, while the target array for which the index is used only has 1 member.

This results in an OOB access to SerialHandle, which leads to an OOB access in `fnRead`.

#### Fix
To remediate this issue, we need to adjust the bounds check to the range 0-0.

Fix idea: Modify the bounds check instructions and index calculation.
- Change the comparison from `<0xb` to `<1`
- Change the expression `10-index` to `0-index`

Patch locations (pre patch):
```
P1_ro:080104DE 0B 28                       CMP     R0, #0xB
P1_ro:080104E0 EC DA                       BGE     loc_80104BC
P1_ro:080104E2 C4 F1 0A 04                 RSB.W   R4, R4, #0xA
P1_ro:080104E6 E4 B2                       UXTB    R4, R4
```

Patch locations (post patch)
```
P1_ro:080104DE 01 28                       CMP     R0, #1
P1_ro:080104E0 EC DA                       BGE     loc_80104BC
P1_ro:080104E2 C4 F1 00 04                 RSB.W   R4, R4, #0
P1_ro:080104E6 E4 B2                       UXTB    R4, R4
```

Binary patches:
```
fnMODBUS_SerialHandle_OOB_index_check:
  description: "Perform the index check to pin it to 0 (instead of the original <=10)"
  address: 0x80104DE
  binfile_offset: 0x445e
  patch_contents: "01"
fnMODBUS_SerialHandle_OOB_index_calc:
  description: "Perform the index calculation by no longer subtracting from 10, but from 0 (which essentially removes the instruction altogether"
  address: 0x80104E4
  binfile_offset: 0x4464
  patch_contents: "00"
```


## GPSTracker

### Bug 1: Unconstrained alloca

#### Bug Description
`USB_SendStringDescriptor` dynamically allocates a stack buffer with a size that bases on fuzzing input without performing a size check.

#### Fix
Fix description: Mask size argument to a single byte to constrain the maximum stack growth to <= 255.

Patching idea:
- Mask size argument register (r1) with 0xff
- As a code cave, use the `delay` function body
- Code cave: Replace the original `delay` with an immediate return to make space for code cave code

Patch locations (pre patch):
```
; Trampoline insertion start
.text:0008424C F8 B5                       PUSH    {R3-R7,LR}
.text:0008424E 01 29                       CMP     R1, #1
.text:00084250 00 AF                       ADD     R7, SP, #0
.text:00084252 06 46                       MOV     R6, R0
.text:00084254 0C 46                       MOV     R4, R1
.text:00084256 28 DD                       BLE     loc_842AA
```

Patch locations (post patch):
```
; Code cave:
.text:00083934 70 47                       BX      LR
.text:00083936 00 AF                       ADD     R7, SP, #0
.text:00083938 06 46                       MOV     R6, R0
.text:0008393A 01 F0 FF 01                 AND.W   R1, R1, #0xFF
.text:0008393E 00 F0 88 BC                 B.W     loc_84252
```

```
; Trampoline
.text:0008424C F8 B5                       PUSH    {R3-R7,LR}
.text:0008424E FF F7 72 BB                 B.W     loc_83936
.text:00084252             ; ---------------------------------------------------------------------------
.text:00084252
.text:00084252             loc_84252                               ; CODE XREF: USB_SendStringDescriptor(uchar const*,int):loc_8393E↑j
.text:00084252 01 29                       CMP     R1, #1
.text:00084254 0C 46                       MOV     R4, R1
.text:00084256 28 DD                       BLE     loc_842AA
```

Binary patches:
```
unconstrained_alloca_code_cave_ret:
  description: "Patch delay function to plain return"
  address: 0x83934
  binfile_offset: 0x3934
  patch_contents: "7047"

unconstrained_alloca_code_cave_contents:
  description: "Repeat overwritten instructions (ADD R7, SP, #0; MOV R6, string;) and mask size with 0xff, then jump back"
  address: 0x83936
  binfile_offset: 0x3936
  patch_contents: "00AF064601f0ff0100f088bc"

unconstrained_alloca_trampoline:
  description: "Trampoline to patch region (delay function + 2) and move conditional branch after trampoline (we are performing the other instructions in the code cave"
  address: 0x8424E
  binfile_offset: 0x424E
  patch_contents: "fff772bb0129"
```


## utasker_MODBUS

### Bug 1: Ethernet ptrRxBd Init Check

#### Bug Description
The issue occurs while checking for new ethernet frames / events in function `fnEthernetEvent`. The function does not check whether the ethernet component has correctly been initialized (more concretely, whether the global variable `ptrRxBd` has successfully been initialized in function `fnConfigEthernet`).

This results in a NULL pointer dereference in `fnEthernetEvent`.

#### Fix
To remediate this issue, we need to check before the use of `ptrRxBd` whether it is non-NULL.


Fix idea: Check the global variable for being NULL.
- Make space for instructions by removing the always-true check fpr `ucEvent != 0xFA` at the beginning of function `fnEthernetEvent`.

Patch locations (pre patch)
```
P1_ro:0800C2EE 00 78                       LDRB    ucEvent, [ucEvent]
P1_ro:0800C2F0 FA 28                       CMP     ucEvent, #0xFA
P1_ro:0800C2F2 18 D1                       BNE     loc_800C326
P1_ro:0800C2F4 DF F8 78 2B                 LDR.W   R2, =ptrRxBd
P1_ro:0800C2F8 10 68                       LDR     R0, [R2]
```

Patch locations (post patch)
```
P1_ro:0800C2EE 00 BF                       NOP
P1_ro:0800C2F0 DF F8 7C 2B                 LDR.W   R2, =ptrRxBd
P1_ro:0800C2F4 10 68                       LDR     R0, [R2]
P1_ro:0800C2F6 00 28                       CMP     R0, #0
P1_ro:0800C2F8 15 D0                       BEQ     loc_800C326
```

Binary patches:
```
ethernet_init_ptrRxBd_check:
  description: "Check ethernet global variable ptrRxBd to be non-NULL before use in fnEthernetEvent"
  address: 0x800C2EE
  binfile_offset: 0x26e
  patch_contents: "00bfdff87c2b1068002815d0"
```

### Bug 2: Flash Arbitrary Write API

#### Bug Description
This is not really a bug, but a feature which allows writing arbitrary values to arbitrary locations via the command line.
This results in potential corruptions of arbitrary memory.

#### Fix
To remediate this issue, we remove all writes that are performed based on the user-provided pointer.

Fix idea: NOP out writes to user-provided pointer

Patch locations (pre patch)
```
P1_ro:0800FE60 39 60                       STR     R1, [R7]
P1_ro:0800FE66 3A 70                       STRB    R2, [R7]
P1_ro:0800FE94 39 80                       STRH    R1, [R7]
P1_ro:0800FE52 FD F7 61 FD                 BL      fnWriteBytesFlash
```

Patch locations (post patch)
```
P1_ro:0800FE60 00 BF                       NOP
P1_ro:0800FE66 00 BF                       NOP
P1_ro:0800FE94 00 BF                       NOP
P1_ro:0800FE52 4F F0 00 00                 MOV.W   R0, #0
```

Binary patches:
```
flash_api_nop_write_1:
  description: "NOP write to user-chosen pointer"
  address: 0x800FE60
  binfile_offset: 0x3de0
  patch_contents: "00bf"

flash_api_nop_write_2:
  description: "NOP write to user-chosen pointer"
  address: 0x800FE66
  binfile_offset: 0x3de6
  patch_contents: "00bf"

flash_api_nop_write_3:
  description: "NOP write to user-chosen pointer"
  address: 0x800FE94
  binfile_offset: 0x3e14
  patch_contents: "00bf"

flash_api_nop_fnWriteBytesFlash_call:
  description: "NOP call to fnWriteBytesFlash with user-chosen pointer"
  address: 0x800FE52
  binfile_offset: 0x3dd2
  patch_contents: "4FF00000"
```

### Bug 3: Ethernet ptrTxBd Init Check

#### Bug Description
The issue occurs while sending ethernet output in function `fnSimulateEthernetIn`. The function does not check whether the ethernet component has correctly been initialized (more concretely, whether the global variable `ptrTxBd` has successfully been initialized in function `fnConfigEthernet`).

This results in a NULL pointer use in `fnSimulateEthernetIn`, which can be turned into an arbitrary read/write in case the NULL page is mapped (which it is for the emulator configuration).

#### Fix
To remediate this issue, we need to check before the use of `ptrTxBd` whether it is non-NULL.

Fix idea: Check the global variable for being NULL.
- Insert a code cave at the end of the file which performs this check.
- Jump to the code cave from `fnSimulateEthernetIn`.

Patch locations (pre patch)
```
P1_ro:0800C77C F8 B5                       PUSH    {R3-R7,LR}      ; Alternative name is '.text_63'
P1_ro:0800C77E 05 46                       MOV     R5, ucData

P1_ro:08016050 <NOT PRESENT in original elf, added by extending ELF section>
```

Patch locations (post patch)
```
P1_ro:0800C77C 09 F0 68 BC                 B.W     fnSimulateEthernetIn_0

P1_ro:08016050             fnSimulateEthernetIn_0
P1_ro:08016050 04 4A                       LDR     R2, =ptrTxBd_0
P1_ro:08016052 12 68                       LDR     R2, [R2]
P1_ro:08016054 00 2A                       CMP     R2, #0
P1_ro:08016056 00 D1                       BNE     loc_801605A
P1_ro:08016058 70 47                       BX      LR
P1_ro:0801605A             ; ---------------------------------------------------------------------------
P1_ro:0801605A
P1_ro:0801605A             loc_801605A                             ; CODE XREF: fnSimulateEthernetIn_0+6↑j
P1_ro:0801605A F8 B5                       PUSH    {R3-R7,LR}
P1_ro:0801605C 05 46                       MOV     R5, R0
P1_ro:0801605E F6 F7 8F BB                 B.W     loc_800C780
P1_ro:0801605E             ; End of function fnSimulateEthernetIn_0
P1_ro:0801605E
P1_ro:0801605E             ; ---------------------------------------------------------------------------
P1_ro:08016062 00                          DCB    0
P1_ro:08016063 BF                          DCB 0xBF
P1_ro:08016064 C8 0A 00 20 off_8016064     DCD ptrTxBd_0
```

Binary patches:
```
fnSimulateEthernetIn_initcheck_reroute:
  description: "Re-route jump to code cave to perform initialization check"
  address: 0x800C77C
  binfile_offset: 0x6fc
  patch_contents: "09F068BC"
fnSimulateEthernetIn_initcheck_codecave:
  description: "Code cave to perform initialization check, and return in case of missing initialization"
  address: 0x08016049
  binfile_offset: 0x9fc9
  patch_contents: "00000000000000044A1268002A00D17047F8B50546F6F78FBB00BFC80A0020"
```

### Bug 4: OOB Array Access on SerialHandle_0
Also see the same Bug in utasker_USB

#### Bug Description
The issue occurs while processing MODBUS frame inputs in function `fnMODBUS`. The function performs a bounds check on the incoming target serial handle index, but checks against a too large bounds. The check is performed for the value <=10, while the target array for which the index is used only has 1 member.

This results in an OOB access to SerialHandle, which leads to an OOB access in `fnRead`.

#### Fix
To remediate this issue, we need to adjust the bounds check to the range 0-0.

Fix idea: Modify the bounds check instructions and index calculation.
- Change the comparison from `<0xb` to `<1`
- Change the expression `10-index` to `0-index`

Patch locations (pre patch)
```
P1_ro:080113F2 0B 28                       CMP     R0, #0xB
P1_ro:080113F4 EC DA                       BGE     loc_80113D0
P1_ro:080113F6 C4 F1 0A 04                 RSB.W   R4, R4, #0xA
P1_ro:080113FA E4 B2                       UXTB    R4, R4
```

Patch locations (post patch)
```
P1_ro:080113F2 01 28                       CMP     R0, #1
P1_ro:080113F4 EC DA                       BGE     loc_80113D0
P1_ro:080113F6 C4 F1 00 04                 RSB.W   R4, R4, #0
P1_ro:080113FA E4 B2                       UXTB    R4, R4
```

Binary patches:
```
fnMODBUS_SerialHandle_OOB_index_check:
  description: "Perform the index check to pin it to 0 (instead of the original <=10)"
  address: 0x80113F2
  binfile_offset: 0x5372
  patch_contents: "01"
fnMODBUS_SerialHandle_OOB_index_calc:
  description: "Perform the index calculation by no longer subtracting from 10, but from 0 (which essentially removes the instruction altogether"
  address: 0x80113F8
  binfile_offset: 0x5378
  patch_contents: "00"
```
