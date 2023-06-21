# Patching HALucinator Targets

## 6LoWPAN_Receiver
The 6LoWPAN_Receiver sample does not seem to have an (easy to trigger) bug which provides control over the program counter.
Thus, no bug seems to meaningfully influence code coverage results (which would be the case if a jump gadget such as a stack-based buffer overflow was present).

### Bug 1: Reassembly Fragment Index OOB
This bug is rather hard to trigger PC control with, but is a known bug which might be triggered and abused for PC control / invalid coverage by advanced fuzzers.

#### Bug Description
The issue occurs during fragment reassembly with too large fragment indices.
The reassembly buffers are of size 0x400 / 1024, with an offset value 8 bit, which is used as an index with a factor of 8.
This results in a maximum index of (8 * 255) + uncomp_hdr_len, which is larger than the allocated buffer size.

#### Fix
To remediate this issue, we need to check before the copy operation whether the index plus the copy length is not pointing out of bounds.

Fix idea: Calculate the end index of the copy operation and compare it to the size of the buffer.
- Make sure the length did not underflow
- Add calculated index with length
- Check for bounds of 1024
- Code cave: Function body of delay_cycles_us, patch delay_cycles_us to return immediately.
- Register assignments: r0: frag_offset\*8+uncomp_hdr_len, r10: uncomp_hdr_len, r2: rx_payload_len, r3: SCRATCH_REG

Patch locations (pre patch)
```
; Within function delay_cycles_us
.text:00000154 30 B5                       PUSH    {R4,R5,LR}
.text:00000156 08 4B                       LDR     R3, =cycles_per_us
.text:00000158 1C 68                       LDR     R4, [R3]
.text:0000015A 08 4A                       LDR     R2, =0xE000E010
.text:0000015C 00 25                       MOVS    R5, #0
.text:0000015E 80 21 49 02                 MOVS    R1, #0x10000

; Within function input()
.text:00004802 D8 00                       LSLS    R0, R3, #3
.text:00004804 50 44                       ADD     R0, R10
.text:00004806 30 18                       ADDS    R0, R6, R0
.text:00004808 74 4B                       LDR     R3, =packetbuf_ptr
```

Patch locations (post patch)
```
; Within function delay_cycles_us
.text:00000154 70 47                       BX      LR
.text:00000156 D8 00                       LSLS    R0, R3, #3
.text:00000158 50 44                       ADD     R0, R10
.text:0000015A 00 2A                       CMP     R2, #0
.text:0000015C 06 DB                       BLT     loc_16C
.text:0000015E 00 EB 02 03                 ADD.W   R3, R0, R2
.text:00000162 B3 F5 80 6F                 CMP.W   R3, #0x400
.text:00000166 01 DC                       BGT     loc_16C
.text:00000168 04 F0 4D BB                 B.W     loc_4806 ; take memcpy
.text:0000016C 04 F0 51 BB                 B.W     loc_4812 ; skip memcpy

; Within function input()
.text:00004802 FB F7 A8 BC                 B.W     loc_156
.text:00004806 30 18                       ADDS    R0, R6, R0
.text:00004808 74 4B                       LDR     R3, =packetbuf_ptr
```


Binary patches:
```
reassembly_frag_oob_code_cave_ret:
  description: "Patch delay_cycles_us function to plain return"
  address: 0x154
  binfile_offset: 0x154
  patch_contents: "7047"

reassembly_frag_oob_code_cave_contents:
  description: "Repeat overwritten instructions (LSLS R0, R3, #3; ADD R0, R10;) and perform checks, then jump back"
  address: 0x156
  binfile_offset: 0x156
  # jumps: 0x168 -> 0x4806, 0x16C -> 0x4812
  patch_contents: "D8005044002a06db00eb0203b3f5806f01dc04f04dbb04f051bb"

reassembly_frag_oob_trampoline:
  description: "Patch jump into code cave (jump from 0x4802 to 0x156)"
  address: 0x4802
  binfile_offset: 0x4802
  patch_contents: "fbf7a8bc"
```


### Bug 2: Infinite Recursion in system_clock_source_get_hz

#### Bug Description
For the `SYSTEM_CLOCK_SOURCE_DFLL` case, `system_clock_source_get_hz` enters a recursion with the following loop: `system_clock_source_get_hz->system_gclk_chan_get_hz->system_gclk_gen_get_hz->system_clock_source_get_hz`.

For too deep recursion, this allows the stack to overflow into the global data section (which will eventually corrupt the program counter for certain call stacks).

#### Fix
To remove the infinite recursion, we remove the recursive call while `system_clock_source_get_hz` handles the `SYSTEM_CLOCK_SOURCE_DFLL` case.

Patch locations (pre patch)
```
.text:00001C46 1B 68                       LDR     R3, [R3]
.text:00001C48 5B 07                       LSLS    R3, R3, #0x1D
.text:00001C4A 01 D4                       BMI     loc_1C50
.text:00001C4C 0F 48                       LDR     R0, =0x2DC6C00
.text:00001C4E 13 E0                       B       locret_1C78
```

Patch locations (post patch)
```
.text:00001C46 1B 68                       LDR     R3, [R3]
.text:00001C48 5B 07                       LSLS    R3, R3, #0x1D
.text:00001C4A 00 BF                       NOP
.text:00001C4C 0F 48                       LDR     R0, =0x2DC6C00
.text:00001C4E 13 E0                       B       locret_1C78
```

Binary patches:
```
system_clock_source_get_hz_recursion:
  description: "Remove the recursion within SYSTEM_CLOCK_SOURCE_DFLL case of system_clock_source_get_hz."
  address: 0x1C4A
  binfile_offset: 0x1C4A
  patch_contents: "00BF"
```
