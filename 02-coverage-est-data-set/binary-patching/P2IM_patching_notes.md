# Patching P2IM Targets

## CNC

### Bug 1: Stack based out of Bounds

#### Bug Description
Affected function: `printFloat`

The function uses a configuration value `settings.decimal_places` to determine the number of digits to print.
The buffer is only allocated with 10 bytes and the bounds of the configuration are never checked.

#### Fix
Fix description: Increase the stack size to make the out of bounds write impossible.

Patching idea:
- The configuration value is a `uint8_t` and can thus never be larger than 255
- If the stack size is increased by 256 bytes a overflow becomes impossible
- Patch the stack adjustment in the prologue and the epilogue
- Swap the mov and add in the epilogue because add with sp can take larger values

Patch locations (pre patch):
```
1. Prologue
0x080038bc      88b0           sub sp, 0x20

2. Epilogue
0x080039fa      00bf           nop
0x080039fc      2037           adds r7, 0x20
0x080039fe      bd46           mov sp, r7
0x08003a00      80bd           pop {r7, pc}
```

Patch locations (post patch)
```
1. Prologue
0x080038bc      c8b0           sub sp, 0x120

2. Epilogue
0x080039fa      00bf           nop
0x080039fc      bd46           mov sp, r7
0x080039fe      48b0           add sp, 0x120
0x08003a00      80bd           pop {r7, pc}
```

Binary patches:
```
oob_stack_sub:
  description: "Increase the stack size from 0x20 to 0x120 to prevent a buffer overflow"
  address: 0x80038bc
  binfile_offset: 0x38bc
  patch_contents: "c8"
oob_stack_add:
  description: "Adjust the stack afterwards"
  address: 0x80039fc
  binfile_offset: 0x39fc
  patch_contents: "bd4648b0"
```

## Gateway

### Known, unpatched Bugs

#### I2C Error handlers do not regard state of the transmit buffer pointer or sizes
Interrupt handler functions such as `I2C_ITError` use and advance `pBuffPtr` without regard to the pointer validity.
This leads to writes to previously invalidated memory. This issue is hard to fix without a major rewrite of the I2C
error handling logic. It also triggers crashes only sporadically, and does not seem to induce invalid coverage.

### Bug 1: Expired pointer use

#### Bug Description
Affected function: `pwm_start`

The function creates an instance of a timer struct on the stack and then passes it to `HAL_TIM_PWM_Init`.
This function stores a pointer to the struct in the global variable `timer_handlers`.
After `pwm_start` returns, the struct becomes invalid.
Later the IRQ handler tries to call a function pointer from the struct, resulting in a crash.
The function pointer can potentially be overwritten with data controlled by the fuzzer, leading to arbitrary control over the pc.

#### Fix
Fix description: Remove the use of the expired variable.

Patching idea:
- A full fix for this issue would be very complicated, as the entire function would need to be replaced
- Run the function unchanged, but don't add the struct to `timer_handlers`

Patch locations (pre patch):
```
1. Call to timer_enable_clock
0x08006e82      00f0fbfa       bl sym.timer_enable_clock
```
Patch mechanic:
- Remove the call to `timer_enable_clock` in `HAL_TIM_PWM_MspInit`
- The struct will no longer be added to `timer_handlers`, avoiding the expired variable use
Patch locations (post patch)
```
1. No call to timer_enable_clock
0x08006e82      00bf           nop
0x08006e84      00bf           nop
```

Binary patches:
```
expired_variable:
  description: "Remove use of expired variable"
  address: 0x08006e82
  binfile_offset: 0x6e82
  patch_contents: "00bf00bf"
```


### Bug 2: Out of bounds write

#### Bug Description
Affected function:
```
void __thiscall firmata::FirmataClass::setPinState(FirmataClass *this,byte pin,int state)
{
  this->pinState[pin] = state;
  return;
}
```
The access to `pinState` is performed without checking the bounds of `pin`.

#### Fix
Fix description: restrict the maximum value of `pin`.

Patching idea:
- return if `pin` is larger than the size of `pinState`
- remove two instructions from the following function `strobeBlinkPin`
   - the arguments `offInterval` and `onInterval` are only passed to `delay`
   - `delay` is an empty function
- patch the calling functions, in this case one function `blinkVersion` with two calls
- add bounds check

Patch locations (pre patch):
```
1. strobeBlinkPin
0x08002fce      2de9f041       push.w {r4, r5, r6, r7, r8, lr}
0x08002fd2      0d46           mov r5, r1
0x08002fd4      1746           mov r7, r2
0x08002fd6      9846           mov r8, r3           ; Load of onInterval
0x08002fd8      069e           ldr r6, [sp, 0x18]   : Load of offInterval
0x08002fda      0024           movs r4, 0

2. blinkVersion
0x08003028      fff7d1ff       bl 0x08002fce
...
0x0800303c      fff7c7ff       bl 0x08002fce

3. setPinState
0x08002fc6      4231           adds r1, 0x42
0x08002fc8      40f82120       str.w r2, [r0, r1, lsl 2]
0x08002fcc      7047           bx lr
```
Patch locations (post patch)
```
1. strobeBlinkPin
0x08002fd2      2de9f041       push.w {r4, r5, r6, r7, r8, lr}
0x08002fd6      0d46           mov r5, r1
0x08002fd8      1746           mov r7, r2
0x08002fda      0024           movs r4, 0

2. blinkVersion
0x08003028      fff7d3ff       bl 0x08002fd2
...
0x0800303c      fff7c9ff       bl 0x08002fd2

3. setPinState
0x08002fc6      3c29           cmp r1, 0x3c
0x08002fc8      02da           bge 0x8002fd0
0x08002fca      4231           adds r1, 0x42
0x08002fcc      40f82120       str.w r2, [r0, r1, lsl 2]
0x08002fd0      7047           bx lr
```

Binary patches:
```
oob_bounds_check:
  description: "Free some space and add bounds check"
  address: 0x08002fc6
  binfile_offset: 0x2fc6
  patch_contents: "3c2902da423140f8212070472de9f0410d461746"
oob_call_fix1:
  description: "Fix first function call"
  address: 0x0800302a
  binfile_offset: 0x302a
  patch_contents: "d3"
oob_call_fix2:
  description: "Fix second function call"
  address: 0x0800303e
  binfile_offset: 0x303e
  patch_contents: "c9"
```


## PLC

### Bug 1: OOB write

#### Bug Description
Affected function:
```
int8_t Modbus::process_FC1( uint16_t *regs, uint8_t u8size )
{
    uint8_t u8currentRegister, u8currentBit, u8bytesno, u8bitsno;
    uint8_t u8CopyBufferSize;
    uint16_t u16currentCoil, u16coil;

    // get the first and last coil from the message
    uint16_t u16StartCoil = word( au8Buffer[ ADD_HI ], au8Buffer[ ADD_LO ] );
    uint16_t u16Coilno = word( au8Buffer[ NB_HI ], au8Buffer[ NB_LO ] );

    // put the number of bytes in the outcoming message
    u8bytesno = (uint8_t) (u16Coilno / 8);
    if (u16Coilno % 8 != 0) u8bytesno ++;
    au8Buffer[ ADD_HI ]  = u8bytesno;
    u8BufferSize         = ADD_LO;

    // read each coil from the register map and put its value inside the outcoming message
    u8bitsno = 0;

    for (u16currentCoil = 0; u16currentCoil < u16Coilno; u16currentCoil++)
    {
        u16coil = u16StartCoil + u16currentCoil;
        // 16 bits per register
        u8currentRegister = (uint8_t) (u16coil / 16);
        u8currentBit = (uint8_t) (u16coil % 16);

        bitWrite(
            au8Buffer[ u8BufferSize ],
            u8bitsno,
            // out of bound read can happen here
            bitRead( regs[ u8currentRegister ], u8currentBit ) );
        u8bitsno ++;

        if (u8bitsno > 7)
        {
            u8bitsno = 0;
            u8BufferSize++;
        }
    }

    // send outcoming message
    // TODO seems not necessary, verify it!
    if (u16Coilno % 8 != 0) u8BufferSize ++;
    u8CopyBufferSize = u8BufferSize +2;
    sendTxBuffer();
    return u8CopyBufferSize;
}
```
In the method `process_FC1` from `Modbus`, the bounds check is performed with user controlled data.
This allows an attacker to overwrite data following the `au8Buffer`.

#### Fix
Fix description: Add bounds check while increasing `u8BufferSize`.

Patching idea:
- create code cave by removing unused function `_sseek`
- add bounds check in code cave

Patch locations (pre patch):
```
1. Increase of u8BufferSize
0x0800094c      94f84930       ldrb.w r3, [r4, 0x49]
0x08000950      0133           adds r3, 1
0x08000952      84f84930       strb.w r3, [r4, 0x49]
0x08000956      0022           movs r2, 0

2. _sseek
0x0800563e      10b5           push {r4, lr}
0x08005640      0c46           mov r4, r1
0x08005642      b1f90e10       ldrsh.w r1, [r1, 0xe]
0x08005646      00f055f8       bl sym._lseek_r
0x0800564a      431c           adds r3, r0, 1
0x0800564c      a389           ldrh r3, [r4, 0xc]
0x0800564e      15bf           itete ne
0x08005650      6065           strne r0, [r4, 0x54]
0x08005652      23f48053       biceq r3, r3, 0x1000
0x08005656      43f48053       orreq r3, r3, 0x1000
0x0800565a      a381           strh r3, [r4, 0xc]
0x0800565c      18bf           it ne
0x0800565e      a381           strhne r3, [r4, 0xc]
0x08005660      10bd           pop {r4, pc}
```
Patch locations (post patch)
```
1. Branch to code cave
0x0800094c      94f84930       ldrb.w r3, [r4, 0x49]
0x08000950      0133           adds r3, 1
0x08000952      04f074be       b.w 0x08005640
0x08000956      0022           movs r2, 0

2. Bounds check in code cave
0x0800563e      7047           bx lr                    ; return, just in case
0x08005640      3e2b           cmp r3, 0x3e             ; 62, because a crc will be added
0x08005642      01da           bge 0x8005648
0x08005644      84f84930       strb.w r3, [r4, 0x49]
0x08005648      fbf785b9       b.w 0x8000956
```

Binary patches:
```
oob_fc1_1:
  description: "Jump to code cave for out of bounds in FC1"
  address: 0x08000952
  binfile_offset: 0x952
  patch_contents: "04f075be"
oob_fc1_2:
  description: "Fix for out of bounds in FC1"
  address: 0x0800563e
  binfile_offset: 0x563e
  patch_contents: "70473e2b01da84f84930fbf785b9"
```

### Bug 2: OOB write

#### Bug Description
Affected function:
```
int8_t Modbus::process_FC3( uint16_t *regs, uint8_t u8size )
{

    uint8_t u8StartAdd = word( au8Buffer[ ADD_HI ], au8Buffer[ ADD_LO ] );
    uint8_t u8regsno = word( au8Buffer[ NB_HI ], au8Buffer[ NB_LO ] );
    uint8_t u8CopyBufferSize;
    uint8_t i;

    au8Buffer[ 2 ]       = u8regsno * 2;
    u8BufferSize         = 3;

    for (i = u8StartAdd; i < u8StartAdd + u8regsno; i++)
    {
        au8Buffer[ u8BufferSize ] = highByte(regs[i]);
        u8BufferSize++;
        au8Buffer[ u8BufferSize ] = lowByte(regs[i]);
        u8BufferSize++;
    }
    u8CopyBufferSize = u8BufferSize +2;
    sendTxBuffer();

    return u8CopyBufferSize;
}
```
In the method `process_FC3` from `Modbus`, the bounds check is performed with user controlled data.
This allows an attacker to overwrite data following the `au8Buffer`.

#### Fix
Fix description: Add bounds check while increasing `u8BufferSize`.

Patching idea:
- code cave, same as above
- add bounds check in code cave
- remove fist store of `u8BufferSize`

Patch locations (pre patch):
```
1. Increase of u8BufferSize
0x080009c2      0133           adds r3, 1
0x080009c4      84f84930       strb.w r3, [r4, 0x49]
0x080009c8      0132           adds r2, 1

2. _sseek
same as above

3. first store of u8BufferSize
0x080009b4      dbb2           uxtb r3, r3
0x080009b6      84f84930       strb.w r3, [r4, 0x49]
0x080009ba      15f81270       ldrb.w r7, [r5, r2, lsl 1]
```
Patch locations (post patch)
```
1. Branch to code cave
0x080009c2      0133           adds r3, 1
0x080009c4      04f042be       b.w 0x800564c
0x080009c8      0132           adds r2, 1

2. Bounds check in code cave
0x0800564c      3d2b           cmp r3, 0x3d                ; 61, increased by two each iteration
0x0800564e      01da           bge 0x8005654
0x08005650      84f84930       strb.w r3, [r4, 0x49]
0x08005654      fbf7b8b9       b.w 0x80009c8

3. first store of u8BufferSize removed
0x080009b4      dbb2           uxtb r3, r3
0x080009b6      00bf           nop
0x080009b8      00bf           nop
0x080009ba      15f81270       ldrb.w r7, [r5, r2, lsl 1]
```

Binary patches:
```
oob_fc3_1:
  description: "Jump to code cave for out of bounds in FC3"
  address: 0x080009c4
  binfile_offset: 0x9c4
  patch_contents: "04f042be"
oob_fc3_2:
  description: "Fix for out of bounds in FC3"
  address: 0x0800564c
  binfile_offset: 0x564c
  patch_contents: "3d2b01da84f84930fbf7b8b9"
oob_fc3_3:
  description: "Remove first store"
  address: 0x080009b6
  binfile_offset: 0x9b6
  patch_contents: "00bf00bf"
```

### Bug 3: OOB write

#### Bug Description
Affected function:
```
int8_t Modbus::process_FC15( uint16_t *regs, uint8_t u8size )
{
    uint8_t u8currentRegister, u8currentBit, u8frameByte, u8bitsno;
    uint8_t u8CopyBufferSize;
    uint16_t u16currentCoil, u16coil;
    boolean bTemp;

    // get the first and last coil from the message
    uint16_t u16StartCoil = word( au8Buffer[ ADD_HI ], au8Buffer[ ADD_LO ] );
    uint16_t u16Coilno = word( au8Buffer[ NB_HI ], au8Buffer[ NB_LO ] );


    // read each coil from the register map and put its value inside the outcoming message
    u8bitsno = 0;
    u8frameByte = 7;
    for (u16currentCoil = 0; u16currentCoil < u16Coilno; u16currentCoil++)
    {

        u16coil = u16StartCoil + u16currentCoil;
        u8currentRegister = (uint8_t) (u16coil / 16);
        u8currentBit = (uint8_t) (u16coil % 16);

        bTemp = bitRead(
                    au8Buffer[ u8frameByte ],
                    u8bitsno );

        bitWrite(
            regs[ u8currentRegister ],
            u8currentBit,
            bTemp );

        u8bitsno ++;

        if (u8bitsno > 7)
        {
            u8bitsno = 0;
            u8frameByte++;
        }
    }

    // send outcoming message
    // it's just a copy of the incomping frame until 6th byte
    u8BufferSize         = 6;
    u8CopyBufferSize = u8BufferSize +2;
    sendTxBuffer();
    return u8CopyBufferSize;
```
In the method `process_FC15` from `Modbus`, the bounds check is performed with user controlled data.
This allows an attacker to overwrite data following the `regs`.

#### Fix
Fix description: Add bounds limit for `u8currentRegister`.

Patching idea:
- limit maximum index value to 4 bit instead of 8

Patch locations (pre patch):
```
1. Extracting 8 bits for the index
0x08000a98      9bb2           uxth r3, r3
0x08000a9a      c3f3071c       ubfx ip, r3, 4, 8
0x08000a9e      03f00f03       and r3, r3, 0xf
```
Patch locations (post patch)
```
1. Extracting 4 bits for the index
0x08000a98      9bb2           uxth r3, r3
0x08000a9a      c3f3031c       ubfx ip, r3, 4, 4
0x08000a9e      03f00f03       and r3, r3, 0xf
```

Binary patches:
```
oob_fc15:
  description: "Fix for out of bounds in FC15"
  address: 0x08000a9c
  binfile_offset: 0xa9c
  patch_contents: "03"
```

### Bug 3: OOB write

#### Bug Description
Affected function:
```
int8_t Modbus::process_FC16( uint16_t *regs, uint8_t u8size )
{
    uint8_t u8func = au8Buffer[ FUNC ];  // get the original FUNC code
    uint8_t u8StartAdd = au8Buffer[ ADD_HI ] << 8 | au8Buffer[ ADD_LO ];
    uint8_t u8regsno = au8Buffer[ NB_HI ] << 8 | au8Buffer[ NB_LO ];
    uint8_t u8CopyBufferSize;
    uint8_t i;
    uint16_t temp;

    // build header
    au8Buffer[ NB_HI ]   = 0;
    au8Buffer[ NB_LO ]   = u8regsno;
    u8BufferSize         = RESPONSE_SIZE;

    // write registers
    for (i = 0; i < u8regsno; i++)
    {
        temp = word(
                   au8Buffer[ (BYTE_CNT + 1) + i * 2 ],
                   au8Buffer[ (BYTE_CNT + 2) + i * 2 ]);

        regs[ u8StartAdd + i ] = temp;
    }
    u8CopyBufferSize = u8BufferSize +2;
    sendTxBuffer();

    return u8CopyBufferSize;
}
```
In the method `process_FC16` from `Modbus`, the bounds check is performed with user controlled data.
This allows an attacker to overwrite data following the `regs`.

#### Fix
Fix description: Add bounds check before using index into `regs`.

Patching idea:
- code cave, same as above
- add bounds check in code cave

Patch locations (pre patch):
```
1. Array access of regs
0x08000b14      3b19           adds r3, r7, r4
0x08000b16      28f81300       strh.w r0, [r8, r3, lsl 1]
0x08000b1a      0134           adds r4, 1

2. _sseek
same as above
```
Patch locations (post patch)
```
1. Branch to code cave
0x08000b14      3b19           adds r3, r7, r4
0x08000b16      04f09fbd       b.w 0x8005658
0x08000b1a      0134           adds r4, 1

2. Bounds check in code cave
0x08005658      082b           cmp r3, 8
0x0800565a      01da           bge 0x8005660
0x0800565c      28f81300       strh.w r0, [r8, r3, lsl 1]
0x08005660      fbf75bba       b.w 0x8000b1a
```

Binary patches:
```
oob_fc16_1:
  description: "Jump to code cave for out of bounds in FC16"
  address: 0x08000b16
  binfile_offset: 0xb16
  patch_contents: "04f09fbd641c"
oob_fc16_2:
  description: "Fix for out of bounds in FC16"
  address: 0x0805658
  binfile_offset: 0x5658
  patch_contents: "082b01da28f81300fbf75bba"
```


## Heat_Press

### Bug 1: Out of bounds write

#### Bug Description
In function `Modbus::get_FC3`, the bounds of the receive buffer is not checked against fix bounds, but
the function relies on user input to perform a bounds check.

#### Fix
Fix description: Restrict the bounds of the write depending on the set of known used buffer addresses/sizes in the firmware image.

Patching idea:
- Update the user-supplied size field based on the output buffer address
- Check the output buffer address against a list of known valid addresses (6 in total)
- Code cave: Overwrite the CRC16 function which is only used for outbound data (and thus not validated/used in firmware code).
- Scratch registers: r6, r7, r3

Patch locations (pre patch)
```
call to Modbus::calcCRC
.text:0008025C 29 46                       MOV     R1, R5          ; u8length
.text:0008025E FF F7 DB FF                 BL      _ZN6Modbus7calcCRCEh
.text:00080262             u16crc = R0                             ; uint16_t

start of Modbus::get_FC3
.text:0008040C F8 B5                       PUSH    {R3-R7,LR}
.text:0008040E 05 46                       MOV     R5, R0

Modbus::calcCRC
.text:00080218 30 B5                       PUSH    {R4,R5,LR}
.text:0008021A 02 46                       MOV     R2, R0
.text:0008021C 4F F6 FF 73                 MOVW    R3, #0xFFFF
.text:00080220 14 1A                       SUBS    R4, R2, R0
...
.text:0008024A 1A 02                       LSLS    R2, R3, #8
.text:0008024C 42 EA 13 20                 ORR.W   R0, R2, R3,LSR#8
.text:00080250 80 B2                       UXTH    R0, R0
.text:00080252 30 BD                       POP     {R4,R5,PC}
```

Patch locations (post patch)
```
Patched-out call to Modbus::calcCRC
.text:0008025C 29 46                       MOV     R1, R5
.text:0008025E 80 EA 00 00                 EOR.W   r0, r0, r0
.text:00080262 63 19                       ADDS    R3, this, R5

Trampoline to code cave in Modbus::get_FC3
.text:0008040C 04 E7                       B       _ZN6Modbus7calcCRCEh
.text:0008040E 05 46                       MOV     R5, R0

Modbus::calcCRC replacement
.text:00080218 F8 B5                       PUSH    {R3-R7,LR}
.text:0008021A C6 6C                       LDR     R6, [R0,#0x4C]
.text:0008021C 0A 49                       LDR     R1, =au16data
.text:0008021E 07 A2                       ADR     R2, arr
.text:00080220 09 A5                       ADR     R5, off_80248
.text:00080222
.text:00080222             loc_80222                               ; CODE XREF: Modbus::calcCRC(uchar)+1E↓j
.text:00080222 AA 42                       CMP     R2, R5
.text:00080224 09 DA                       BGE     loc_8023A
.text:00080226 17 78                       LDRB    R7, [R2]
.text:00080228 8E 42                       CMP     R6, R1
.text:0008022A 05 D0                       BEQ     loc_80238
.text:0008022C 53 78                       LDRB    R3, [R2,#1]
.text:0008022E 39 44                       ADD     R1, R7
.text:00080230 19 44                       ADD     R1, R3
.text:00080232 02 F1 02 02                 ADD.W   R2, R2, #2
.text:00080236 F4 E7                       B       loc_80222
.text:00080238             ; ---------------------------------------------------------------------------
.text:00080238
.text:00080238             loc_80238                               ; CODE XREF: Modbus::calcCRC(uchar)+12↑j
.text:00080238 C7 72                       STRB    R7, [R0,#0xB]
.text:0008023A
.text:0008023A             loc_8023A                               ; CODE XREF: Modbus::calcCRC(uchar)+C↑j
.text:0008023A E8 E0                       B       loc_8040E
.text:0008023A             ; End of function Modbus::calcCRC(uchar)
.text:0008023A
.text:0008023A             ; ---------------------------------------------------------------------------
.text:0008023C             ; char arr[2][6]
.text:0008023C 26 00 02 00+arr             DCW 0x26, 2, 0x10, 0xC008, 2, 0x12
.text:0008023C 10 00 08 C0+                                        ; DATA XREF: Modbus::calcCRC(uchar)+6↑o
.text:0008023C 02 00 12 00                                         ; Modbus::calcCRC(uchar)+E↑r ...
.text:00080248 C8 08 07 20 off_80248       DCD au16data
```

Binary Patches:
```
oob_bounds_check_remove_crc16_call:
  description: "remove the call to crc16 and replace it with a zero result"
  address: 0x8025E
  binfile_offset: 0x25E
  patch_contents: "80ea0000"
oob_bounds_check_jump_to_code_cave:
  description: "insert branch into code cave (previously crc16 function)"
  address: 0x8040C
  binfile_offset: 0x40C
  # jump 8040C -> 80218
  patch_contents: "04e7"
oob_bounds_check_code_cave_contents:
  description: "Use code cave to patch the user-provided input size into bounds"
  address: 0x80218
  binfile_offset: 0x218
  patch_contents: "f8b5c66c0a4907a209a5aa4209da17788e4205d053783944194402f10202f4e7c772e8e026000200100008c002001200c8080720"
```


## Soldering_Iron

### Bug 1: Expired Pointer Use
Also see other expired pointer use bug (Bug 1 of Gateway)

#### Bug Description
As the `HAL_I2C_Mem_Read` function does not clear the I2C handle's buffer and the interrupt-context function `I2C_MasterReceive_BTF`
does not check locks or the liveness of pointers, already invalidated pointers can be used.

#### Fix
Fix description: Once `I2C_MasterReceive_BTF` returns, set the pointer to a (near) NULL value where data can safely be written to. While
this may not entirely be correct behavior, it should prevent any memory corruptions from dangling pointers.

Patching idea:
- Upon `HAL_I2C_Mem_Read` return, write a near-zero value to the pointer member
- Make space for two instructions by
  - using two currently unused alignment bytes
  - saving one instruction (`mov r0, r3`) by directly assigning the return value to `r0` instead of `r3` in all instances (11 instances, though...)


Patch locations (pre patch)
```
.text:0800C5B4 02 23                       MOVS    R3, #2
.text:0800C5B6 F8 E1                       B       loc_800C9AA

.text:0800C5C2 02 23                       MOVS    R3, #2
.text:0800C5C4 F1 E1                       B       loc_800C9AA

.text:0800C65A 01 23                       MOVS    R3, #1
.text:0800C65C A5 E1                       B       loc_800C9AA

.text:0800C666 03 23                       MOVS    R3, #3
.text:0800C668 9F E1                       B       loc_800C9AA

.text:0800C774 03 23                       MOVS    R3, #3
.text:0800C776 18 E1                       B       loc_800C9AA

.text:0800C778 01 23                       MOVS    R3, #1
.text:0800C77A 16 E1                       B       loc_800C9AA

.text:0800C884 03 23                       MOVS    R3, #3
.text:0800C886 90 E0                       B       loc_800C9AA

.text:0800C910 03 23                       MOVS    R3, #3
.text:0800C912 4A E0                       B       loc_800C9AA

.text:0800C914 01 23                       MOVS    R3, #1
.text:0800C916 48 E0                       B       loc_800C9AA

.text:0800C9A4 00 23                       MOVS    R3, #0
.text:0800C9A6 00 E0                       B       loc_800C9AA

.text:0800C9A8 02 23                       MOVS    R3, #2

.text:0800C9AA 18 46                       MOV     R0, R3
.text:0800C9AC 28 37                       ADDS    R7, #0x28 ; '('
.text:0800C9AE BD 46                       MOV     SP, R7
.text:0800C9B0 80 BD                       POP     {R7,PC}
.text:0800C9B2 00 BF                       ALIGN 4
```

Patch locations (post patch)
```
.text:0800C5B4 02 20                       MOVS    R0, #2
.text:0800C5B6 F8 E1                       B       loc_800C9AA

.text:0800C5C2 02 20                       MOVS    R0, #2
.text:0800C5C4 F1 E1                       B       loc_800C9AA

.text:0800C65A 01 20                       MOVS    R0, #1
.text:0800C65C A5 E1                       B       loc_800C9AA

.text:0800C666 03 20                       MOVS    R0, #3
.text:0800C668 9F E1                       B       loc_800C9AA

.text:0800C774 03 20                       MOVS    R0, #3
.text:0800C776 18 E1                       B       loc_800C9AA

.text:0800C778 01 20                       MOVS    R0, #1
.text:0800C77A 16 E1                       B       loc_800C9AA

.text:0800C884 03 20                       MOVS    R0, #3
.text:0800C886 90 E0                       B       loc_800C9AA

.text:0800C910 03 20                       MOVS    R0, #3
.text:0800C912 4A E0                       B       loc_800C9AA

.text:0800C914 01 20                       MOVS    R0, #1
.text:0800C916 48 E0                       B       loc_800C9AA

.text:0800C9A4 00 20                       MOVS    R0, #0
.text:0800C9A6 00 E0                       B       loc_800C9AA

.text:0800C9A8 02 20                       MOVS    R0, #2
.text:0800C9AA FB 68                       LDR     R3, [R7,#0x28+hi2c]
.text:0800C9AC 58 62                       STR     R0, [R3,#0x24]
.text:0800C9AE 28 37                       ADDS    R7, #0x28
.text:0800C9B0 BD 46                       MOV     SP, R7
.text:0800C9B2 80 BD                       POP     {R7,PC}
```

Instructions to set the pointer:
```
LDR R3, [R7,#0xC]
str r0, [r3, #0x24]
```

Binary patches
```
expired_pointer_use_ret_val_1:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C5B5
  binfile_offset: 0xC5B5
  patch_contents: "20"
expired_pointer_use_ret_val_2:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C5C3
  binfile_offset: 0xC5C3
  patch_contents: "20"
expired_pointer_use_ret_val_3:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C65B
  binfile_offset: 0xC65B
  patch_contents: "20"
expired_pointer_use_ret_val_4:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C667
  binfile_offset: 0xC667
  patch_contents: "20"
expired_pointer_use_ret_val_5:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C775
  binfile_offset: 0xC775
  patch_contents: "20"
expired_pointer_use_ret_val_6:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C779
  binfile_offset: 0xC779
  patch_contents: "20"
expired_pointer_use_ret_val_7:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C885
  binfile_offset: 0xC885
  patch_contents: "20"
expired_pointer_use_ret_val_8:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C911
  binfile_offset: 0xC911
  patch_contents: "20"
expired_pointer_use_ret_val_9:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C915
  binfile_offset: 0xC915
  patch_contents: "20"
expired_pointer_use_ret_val_10:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C9A5
  binfile_offset: 0xC9A5
  patch_contents: "20"

expired_pointer_use_modified_epilogue:
  description: "add an override of the destination buffer stored in the I2C handle pBuffPtr field"
  address: 0x800C9A8
  binfile_offset: 0xC9A8
  patch_contents: "0220fb6858622837bd4680bd"
```

### Bug 2: Integer Underflow into OOB Write in OLED::drawHeatSymbol

#### Bug Description
The value returned from `getTipPWM` is used as the `state` argument value in a call to `OLED::drawHeatSymbol` from `gui_solderingMode`.

`OLED::drawHeatSymbol` does not check the bounds of the value of `state`, which leads to an integer underflow when passing the expression
`10 - (getTipPWM() / 0xc)` to `OLED::drawFilledRect` as the `y1` argument in case `state>132`. As `OLED::drawFilledRect` itself also does not
perform any bounds checks, a buffer overflow occurs while writing to the `led` frame buffer (which has a fixed size of 200).

#### Fix
Fix description: Ensure bounds of the value passed as `y1` into the `OLED::drawFilledRect` function.

Patching idea:
- Mask the value of `y1` by 0xf such that the index expression `y>>3` always stays within expected bounds `0-1` in `OLED::drawFilledRect`.
- Note that this patch changes the mapping of `state` argument to `y1` index, so it does not exactly preserve how specific state values would be drawn on the screen.

Patch locations (pre patch)
```
.text:08000F0A FB 78                       LDRB    R3, [R7,#0x10+state]
.text:08000F0C C3 F1 0A 03                 RSB.W   R3, R3, #0xA
.text:08000F10 DB B2                       UXTB    R3, R3
.text:08000F12 F9 7B                       LDRB    R1, [R7,#0x10+cursor_x_temp] ; x0
.text:08000F14 01 22                       MOVS    R2, #1
.text:08000F16 01 92                       STR     R2, [SP,#0x18+clear] ; clear
.text:08000F18 00 93                       STR     R3, [SP,#0x18+y1] ; y1
```

Patch locations (post patch)
```
.text:08000F0A FB 78                       LDRB    R3, [R7,#0x10+state]
.text:08000F0C 03 F0 0F 03                 AND.W   R3, R3, #0xF
.text:08000F10 DB B2                       UXTB    R3, R3
.text:08000F12 F9 7B                       LDRB    R1, [R7,#0x10+cursor_x_temp] ; x0
.text:08000F14 01 22                       MOVS    R2, #1
.text:08000F16 01 92                       STR     R2, [SP,#0x18+clear] ; clear
.text:08000F18 00 93                       STR     R3, [SP,#0x18+y1] ; y1
```

Binary patches
```
constrain_draw_index:
  description: "Mask the state value which will be passed as y1 index with 0xf to ensure the correct range"
  address: 0x08000F0C
  binfile_offset: 0xF0C
  patch_contents: "03f00f03"
```


### Bug 3: Expired Pointer Use in I2C_ITError
Also see other expired pointer use bug (Bug 1 of Soldering_Iron)

#### Bug Description
As the `HAL_I2C_Mem_Write` function does not clear the I2C handle's buffer and the interrupt-context function `I2C_MasterReceive_RXNE`
does not check locks or the liveness of pointers, already invalidated pointers can be used.

In addition, the error handler function `I2C_ITError` does not perform any checks on the transfer size or of pointer validity.

#### Fix
Fix description: Once `HAL_I2C_Mem_Write` returns, set the pointer to a (near) NULL value where data can safely be written to. While
this may not entirely be correct behavior, it should prevent any memory corruptions from dangling pointers. Regarding `I2C_ITError`, also remove the write and pointer increments. This also is not pure firmware behavior, but only regards the writing of a single byte in the I2C transmission error case.

Patching idea:
- Upon `HAL_I2C_Mem_Write` return, write a near-zero value to the pointer member
- Make space for two instructions by
  - using two currently unused alignment bytes
  - saving one instruction (`mov r0, r3`) by directly assigning the return value to `r0` instead of `r3` in all instances (10 instances, though...)
- Regarding `I2C_ITError`, NOP out the data-write-and-increment

Patch locations (pre patch)
```
.text:0800B010 7B 68                       LDR     R3, [R7,#0x10+hi2c]
.text:0800B012 5B 6A                       LDR     R3, [R3,#0x24]
.text:0800B014 59 1C                       ADDS    R1, R3, #1
.text:0800B016 7A 68                       LDR     R2, [R7,#0x10+hi2c]
.text:0800B018 51 62                       STR     R1, [R2,#0x24]
.text:0800B01A 7A 68                       LDR     R2, [R7,#0x10+hi2c]
.text:0800B01C 12 68                       LDR     R2, [R2]
.text:0800B01E 12 69                       LDR     R2, [R2,#0x10]
.text:0800B020 D2 B2                       UXTB    R2, R2
.text:0800B022 1A 70                       STRB    R2, [R3]

.text:0800B074 7B 68                       LDR     R3, [R7,#0x10+hi2c]
.text:0800B076 5B 6A                       LDR     R3, [R3,#0x24]
.text:0800B078 59 1C                       ADDS    R1, R3, #1
.text:0800B07A 7A 68                       LDR     R2, [R7,#0x10+hi2c]
.text:0800B07C 51 62                       STR     R1, [R2,#0x24]
.text:0800B07E 7A 68                       LDR     R2, [R7,#0x10+hi2c]
.text:0800B080 12 68                       LDR     R2, [R2]
.text:0800B082 12 69                       LDR     R2, [R2,#0x10]
.text:0800B084 D2 B2                       UXTB    R2, R2
.text:0800B086 1A 70                       STRB    R2, [R3]

.text:0800B0AE 7B 68                       LDR     R3, [R7,#0x10+hi2c]
.text:0800B0B0 5B 6A                       LDR     R3, [R3,#0x24]
.text:0800B0B2 59 1C                       ADDS    R1, R3, #1
.text:0800B0B4 7A 68                       LDR     R2, [R7,#0x10+hi2c]
.text:0800B0B6 51 62                       STR     R1, [R2,#0x24]
.text:0800B0B8 7A 68                       LDR     R2, [R7,#0x10+hi2c]
.text:0800B0BA 12 68                       LDR     R2, [R2]
.text:0800B0BC 12 69                       LDR     R2, [R2,#0x10]
.text:0800B0BE D2 B2                       UXTB    R2, R2
.text:0800B0C0 1A 70                       STRB    R2, [R3]

.text:0800C558 02 23                       MOVS    R3, #2

.text:0800C554 00 23                       MOVS    R3, #0
.text:0800C556 00 E0                       B       loc_800C55A

.text:0800C528 03 23                       MOVS    R3, #3
.text:0800C52A 16 E0                       B       loc_800C55A

.text:0800C524 01 23                       MOVS    R3, #1
.text:0800C526 18 E0                       B       loc_800C55A

.text:0800C482 03 23                       MOVS    R3, #3
.text:0800C484 69 E0                       B       loc_800C55A

.text:0800C47E 01 23                       MOVS    R3, #1
.text:0800C480 6B E0                       B       loc_800C55A

.text:0800C452 03 23                       MOVS    R3, #3
.text:0800C454 81 E0                       B       loc_800C55A

.text:0800C446 01 23                       MOVS    R3, #1
.text:0800C448 87 E0                       B       loc_800C55A

.text:0800C3AE 02 23                       MOVS    R3, #2
.text:0800C3B0 D3 E0                       B       loc_800C55A

.text:0800C3A0 02 23                       MOVS    R3, #2
.text:0800C3A2 DA E0                       B       loc_800C55A
```

Patch locations (post patch)
```
.text:0800B010 00 BF                       NOP
.text:0800B012 00 BF                       NOP
.text:0800B014 00 BF                       NOP
.text:0800B016 00 BF                       NOP
.text:0800B018 00 BF                       NOP
.text:0800B01A 00 BF                       NOP
.text:0800B01C 00 BF                       NOP
.text:0800B01E 00 BF                       NOP
.text:0800B020 00 BF                       NOP
.text:0800B022 00 BF                       NOP

.text:0800B074 00 BF                       NOP
.text:0800B076 00 BF                       NOP
.text:0800B078 00 BF                       NOP
.text:0800B07A 00 BF                       NOP
.text:0800B07C 00 BF                       NOP
.text:0800B07E 00 BF                       NOP
.text:0800B080 00 BF                       NOP
.text:0800B082 00 BF                       NOP
.text:0800B084 00 BF                       NOP
.text:0800B086 00 BF                       NOP

.text:0800B0AE 00 BF                       NOP
.text:0800B0B0 00 BF                       NOP
.text:0800B0B2 00 BF                       NOP
.text:0800B0B4 00 BF                       NOP
.text:0800B0B6 00 BF                       NOP
.text:0800B0B8 00 BF                       NOP
.text:0800B0BA 00 BF                       NOP
.text:0800B0BC 00 BF                       NOP
.text:0800B0BE 00 BF                       NOP
.text:0800B0C0 00 BF                       NOP

.text:0800C558 02 20                       MOVS    R0, #2

.text:0800C554 00 20                       MOVS    R0, #0
.text:0800C556 00 E0                       B       loc_800C55A

.text:0800C528 03 20                       MOVS    R0, #3
.text:0800C52A 16 E0                       B       loc_800C55A

.text:0800C524 01 20                       MOVS    R0, #1
.text:0800C526 18 E0                       B       loc_800C55A

.text:0800C482 03 20                       MOVS    R0, #3
.text:0800C484 69 E0                       B       loc_800C55A

.text:0800C47E 01 20                       MOVS    R0, #1
.text:0800C480 6B E0                       B       loc_800C55A

.text:0800C452 03 20                       MOVS    R0, #3
.text:0800C454 81 E0                       B       loc_800C55A

.text:0800C446 01 20                       MOVS    R0, #1
.text:0800C448 87 E0                       B       loc_800C55A

.text:0800C3AE 02 20                       MOVS    R0, #2
.text:0800C3B0 D3 E0                       B       loc_800C55A

.text:0800C3A0 02 20                       MOVS    R0, #2
.text:0800C3A2 DA E0                       B       loc_800C55A
```

Binary patches
```
I2C_ITError_remove_write_1:
  description: "Remove the unchecked write-and-increment-pointer which is performed in I2C_ITError isr."
  address: 0x0800B010
  binfile_offset: 0xB010
  patch_contents: "00bf00bf00bf00bf00bf00bf00bf00bf00bf00bf"
I2C_ITError_remove_write_2:
  description: "Remove the unchecked write-and-increment-pointer which is performed in I2C_ITError isr."
  address: 0x0800B074
  binfile_offset: 0xB074
  patch_contents: "00bf00bf00bf00bf00bf00bf00bf00bf00bf00bf"
I2C_ITError_remove_write_3:
  description: "Remove the unchecked write-and-increment-pointer which is performed in I2C_ITError isr."
  address: 0x0800B0AE
  binfile_offset: 0xB0AE
  patch_contents: "00bf00bf00bf00bf00bf00bf00bf00bf00bf00bf"

expired_pointer_2_use_ret_val_1:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C559
  binfile_offset: 0xC559
  patch_contents: "20"
expired_pointer_2_use_ret_val_2:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C555
  binfile_offset: 0xC555
  patch_contents: "20"
expired_pointer_2_use_ret_val_3:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C529
  binfile_offset: 0xC529
  patch_contents: "20"
expired_pointer_2_use_ret_val_4:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C525
  binfile_offset: 0xC525
  patch_contents: "20"
expired_pointer_2_use_ret_val_5:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C483
  binfile_offset: 0xC483
  patch_contents: "20"
expired_pointer_2_use_ret_val_6:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C47f
  binfile_offset: 0xC47f
  patch_contents: "20"
expired_pointer_2_use_ret_val_7:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C453
  binfile_offset: 0xC453
  patch_contents: "20"
expired_pointer_2_use_ret_val_8:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C447
  binfile_offset: 0xC447
  patch_contents: "20"
expired_pointer_2_use_ret_val_9:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C3AF
  binfile_offset: 0xC3AF
  patch_contents: "20"
expired_pointer_2_use_ret_val_10:
  description: "directly assign r0 value instead of r3"
  address: 0x0800C3A1
  binfile_offset: 0xC3A1
  patch_contents: "20"
expired_pointer_2_use_modified_epilogue:
  description: "add an override of the destination buffer stored in the I2C handle pBuffPtr field"
  address: 0x0800C55A
  binfile_offset: 0xC55A
  patch_contents: "FB6858621837BD4680BD"
```
