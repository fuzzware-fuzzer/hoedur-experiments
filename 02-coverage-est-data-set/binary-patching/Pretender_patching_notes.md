# Patching Pretender Targets

## RF_Door_Lock

### Bug 1: Stack-based Buffer Overflow In set_code

#### Bug Description
Vulnerable function:
```
void __fastcall set_code(int a1, int a2, int a3, int a4)
{
  int i; // r4
  int v5; // r0
  char c; // r0
  char buf[24]; // [sp+0h] [bp-18h] BYREF

  *(_DWORD *)buf = a1;
  *(_DWORD *)&buf[4] = a2;
  *(_DWORD *)&buf[8] = a3;
  *(_DWORD *)&buf[12] = a4;
  for ( i = 0; ; ++i )
  {
    do
      mbed::SerialBase::readable();
    while ( !v5 );
    c = mbed::Stream::getc();
    buf[i] = c;
    if ( c == '\n' )
      break;
  }
  buf[i] = 0;
  ...
}
```
Stack buffer is written to without bounds check in function `set_codev`.
Address of write in loop: `0x428`.

#### Fix
Fix description: Change the loop escape condition from newline check to a fixed size limitation.

Patching idea:
- Same as for Thermostat
- Change comparison of character to newline to comparison of output index with maximum size
- Register `r4` used as index, so change comparison instruction against `r0` (character value) to a comparison with `r4`

Patch locations (pre patch):
```
.text:00000426 0A 28                       CMP     R0, #0xA
.text:00000428 0D F8 04 00                 STRB.W  R0, [SP,R4]
.text:0000042C 0E D1                       BNE     loc_44C
```

Patch locations (post patch):
```
.text:00000426 06 2C                       CMP     R4, #6
.text:00000428 0D F8 04 00                 STRB.W  R0, [SP,R4]
.text:0000042C 0E D1                       BNE     loc_44C
```

Binary patches:
```
stackbuf_length_check:
  description: "Change the newline-based exit condition to an index-based bounds restriction"
  address: 0x426
  binfile_offset: 0x426
  patch_contents: "062c"
```

### Bug 2: Infinite Recursion In Serial Interface Init Error Case

#### Bug Description
An infinite recursion can occur if an assertion is triggered during Serial Interface initialization, as the assertion handler again tries to initialize the serial interface.

Infinite recursion stack frame: `pin_function->mbed_assert_internal->mbed_error_printf->mbed_error_vfprintf->serial_init->pinmap_pinout->pin_function`.

#### Fix
Fix description: Prevent the assertion function from using the serial interface.

Patching idea: Make `mbed_assert_internal` no longer call `mbed_error_printf`. NOP out the call instruction.

Patch location (pre patch):
```
.text:00001894 33 46                       MOV     R3, R6
.text:00001896 2A 46                       MOV     R2, R5
.text:00001898 21 46                       MOV     R1, R4
.text:0000189A 03 48                       LDR     R0, =dword_8B8C
.text:0000189C FE F7 3C FF                 BL      mbed_error_printf
```

Patch location (post patch):
```
.text:00001894 33 46                       MOV     R3, R6
.text:00001896 2A 46                       MOV     R2, R5
.text:00001898 21 46                       MOV     R1, R4
.text:0000189A 03 48                       LDR     R0, =dword_8B8C
.text:0000189C 00 BF                       NOP
.text:0000189E 00 BF                       NOP
```

Binary patches:
```
infinite_recursion_serial_init_error:
  description: "In mbed_assert_internal, NOP out the call to mbed_error_printf"
  address: 0x189C
  binfile_offset: 0x189C
  patch_contents: "00bf00bf"
```

### Bug 3: Stack-based Buffer Overflow In read_code

#### Bug Description
Vulnerable function:
```
void read_code()
{
  char *cursor; // r4
  char c; // r0
  char v2; // [sp+7h] [bp-21h] BYREF
  char buf[16]; // [sp+8h] [bp-20h] BYREF

  v2 = -52;
  cursor = &v2;
  do
  {
    while ( !mbed::SerialBase::readable() )
      ;
    c = mbed::Stream::getc();
    *++cursor = c;
  }
  while ( c );
  if ( !strcmp(buf, the_pw) )
  {
    rf_write_buf();
  }
  else
  {
    rf_write_buf();
    unlock();
  }
}
```
Stack buffer is written to without bounds check in function `read_code`.
Address of write in loop: `0x3d6`.

#### Fix
Fix description: Change the loop escape condition to a fixed size limitation.

Patching idea:
- create variable by assigning a constant (0xdd) to a callee-saved register (r7)
- create loop bound by
  - subtracting ceil(0xdd/6) in a sign operation
  - changing loop jump condition to positive / signed greater equal zero

Patch locations (pre patch):
```
.text:000003B0 30 B5                       PUSH    {R4,R5,LR}
.text:000003B2 DD 23                       MOVS    R3, #0xDD
.text:000003B4 87 B0                       SUB     SP, SP, #0x1C
.text:000003B6 06 AC                       ADD     R4, SP, #0x30+var_18
.text:000003B8 8D F8 06 30                 STRB.W  R3, [SP,#0x30+var_2A]

.text:000003D4 C0 B2                       UXTB    R0, R0
.text:000003D6 04 F8 01 0F                 STRB.W  R0, [R4,#1]!
.text:000003DA 00 28                       CMP     R0, #0
.text:000003DC F2 D1                       BNE     loc_3C4

.text:00000400 07 B0                       ADD     SP, SP, #0x1C
.text:00000402 30 BD                       POP     {R4,R5,PC}
```

Patch locations (post patch):
```
.text:000003B0 F0 B5                       PUSH    {R4-R7,LR}
.text:000003B2 DD 27                       MOVS    R7, #0xDD
.text:000003B4 87 B0                       SUB     SP, SP, #0x1C
.text:000003B6 06 AC                       ADD     R4, SP, #0x30+var_18
.text:000003B8 8D F8 06 70                 STRB.W  R7, [SP,#0x30+var_2A]

.text:000003D4 C0 B2                       UXTB    R0, R0
.text:000003D6 04 F8 01 0F                 STRB.W  R0, [R4,#1]!
.text:000003DA 24 3F                       SUBS    R7, #0x24 ; '$'
.text:000003DC F2 D5                       BPL     loc_3C4

.text:00000400 07 B0                       ADD     SP, SP, #0x1C
.text:00000402 F0 BD                       POP     {R4-R7,PC}
```

Binary patches:
```
read_code_buffer_check_function_prologue:
  description: "Save r7 on the stack and set r7 to constant instead of r3"
  address: 0x000003B0
  binfile_offset: 0x000003B0
  patch_contents: "f0b5dd27"

read_code_buffer_check_constant_byte_write:
  description: "Write value in r7 instead of r3"
  address: 0x000003Bb
  binfile_offset: 0x000003Bb
  patch_contents: "70"

read_code_buffer_loop_condition:
  description: "Subtract ceil(0xdd/6)=36 and check for positivity to create loop bounds"
  address: 0x000003DA
  binfile_offset: 0x000003DA
  patch_contents: "243ff2d5"

read_code_buffer_check_function_epilogue:
  description: "Restore r7"
  address: 0x00000402
  binfile_offset: 0x00000402
  patch_contents: "f0"
```


## Thermostat

### Bug 1: Stack-based Buffer Overflow

#### Bug Description
Vulnerable function:
```
void __fastcall get_new_temp(int a1, int a2, int a3, int a4, unsigned __int8 a5, int a6, int a7, int a8, int a9) {
  int i; // r4
  char c; // r0
  float v11; // r0
  char buf[24]; // [sp+0h] [bp-18h] BYREF

  *(_DWORD *)buf = a1;
  *(_DWORD *)&buf[4] = a2;
  *(_DWORD *)&buf[8] = a3;
  *(_DWORD *)&buf[12] = a4;
  for ( i = 0; ; ++i )
  {
    do
    {
      while ( !mbed::SerialBase::readable() )
        ;
      c = mbed::Stream::getc();
    }
    while ( !c );
    if ( c == 13 ) // <====== getc() - like input read
      break;
    buf[i] = c;
  }
  buf[i] = 0;
```
Stack buffer is written to without bounds check in function `get_new_temp`.
Address of write in loop: `0x000003CE`.

#### Fix
Fix description: Change the loop escape condition from newline check to a fixed size limitation.

Patching idea:
- Change comparison of character to newline to comparison of output index with maximum size
- Register `r4` used as index, so change comparison instruction against `r0` (character value) to a comparison with `r4`

Patch locations (pre patch):
```
.text:000003CA 0D 28                       CMP     R0, #0xD
.text:000003CC 03 D0                       BEQ     loc_3D6
```

Patch locations (post patch):
```
.text:000003CA 07 2C                       CMP     R4, #7
.text:000003CC 03 D0                       BEQ     loc_3D6
```

Binary patches:
```
stackbuf_length_check:
    description: "Change the newline-based exit condition to an index-based bounds restriction"
    address: 0x3CA
    binfile_offset: 0x3CA
    patch_contents: "072c"
```
