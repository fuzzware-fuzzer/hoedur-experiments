# Patching WYCINWYC Targets

## XML_Parser
Based on the XML input size, bugs of different types are triggered (Stack-based Buffer Overflow, NULL pointer dereference, use-after-free, format string).

### Bug 1: Stack-based Buffer Overflow

#### Bug Description
Synthetic vulnerability, [original source](https://github.com/avatartwo/ndss18_wycinwyc/blob/master/target_source/expatlib/xmlparse.c#L1620)

#### Fix
Patch Location (pre patch)
```
.text:0800B67A 40 F2 C6 43                 MOVW    R3, #0x4C6
.text:0800B67E 9E 42                       CMP     len, R3
.text:0800B680 08 D1                       BNE     loc_800B694
```

```
.text:0800B67A 40 F2 C6 43                 MOVW    R3, #0x4C6
.text:0800B67E 9E 42                       CMP     len, R3
.text:0800B680 08 E0                       B       loc_800B694
```

Binary patches:
```
len_based_bug_trigger_1_stack_based_bof:
  description: "Do not trigger bug case by making branch unconditional"
  address: 0x800B681
  binfile_offset: 0xB681
  patch_contents: "e0"
```

### Bug 2: NULL Pointer Dereference

#### Bug Description
Synthetic vulnerability, [original source](https://github.com/avatartwo/ndss18_wycinwyc/blob/master/target_source/expatlib/xmlparse.c#L1626)

#### Fix
Patch Location (pre patch)
```
.text:0800B694 40 F2 C7 43                 MOVW    R3, #0x4C7
.text:0800B698 9E 42                       CMP     len, R3
.text:0800B69A 0E D0                       BEQ     loc_800B6BA
```

Patch Location (post patch)
```
.text:0800B694 40 F2 C7 43                 MOVW    R3, #0x4C7
.text:0800B698 9E 42                       CMP     len, R3
.text:0800B69A 00 BF                       NOP
```

Binary patches:
```
len_based_bug_trigger_2_null_pointer_dereference:
  description: "Do not trigger bug case by NOP'ing triggering branch instruction"
  address: 0x800B69A
  binfile_offset: 0xB69A
  patch_contents: "00bf"
```

### Bug 3: Heap-based Buffer Overflow

#### Bug Description
Synthetic vulnerability, [original source](https://github.com/avatartwo/ndss18_wycinwyc/blob/master/target_source/expatlib/xmlparse.c#L1630)

#### Fix
Patch Location (pre patch)
```
.text:0800B69C 40 F2 C9 43                 MOVW    R3, #0x4C9
.text:0800B6A0 9E 42                       CMP     len, R3
.text:0800B6A2 0B D1                       BNE     loc_800B6BC
```

Patch Location (post patch)
```
.text:0800B69C 40 F2 C9 43                 MOVW    R3, #0x4C9
.text:0800B6A0 9E 42                       CMP     len, R3
.text:0800B6A2 0B E0                       B       loc_800B6BC
```

Binary patches:
```
len_based_bug_trigger_3_heap_based_bof:
  description: "Do not trigger bug case by making branch unconditional"
  address: 0x800B6A3
  binfile_offset: 0xB6A3
  patch_contents: "e0"
```

### Bug 4: Format String Injection

#### Bug Description
Synthetic vulnerability, [original source](https://github.com/avatartwo/ndss18_wycinwyc/blob/master/target_source/expatlib/xmlparse.c#L1638)

#### Fix
Patch Location (pre patch)
```
.text:0800B6C6 B6 F5 99 6F                 CMP.W   len, #0x4C8
.text:0800B6CA 02 D1                       BNE     loc_800B6D2
```

Patch Location (post patch)
```
.text:0800B6C6 B6 F5 99 6F                 CMP.W   len, #0x4C8
.text:0800B6CA 02 E0                       B       loc_800B6D2
```

Binary patches:
```
len_based_bug_trigger_4_format_string:
  description: "Do not trigger bug case by making branch unconditional"
  address: 0x800B6CB
  binfile_offset: 0xB6CB
  patch_contents: "e0"
```


### Bug 5: Double Free

#### Bug Description
Synthetic vulnerability, [original source](https://github.com/avatartwo/ndss18_wycinwyc/blob/master/target_source/expatlib/xmlparse.c#L1764)

#### Fix
Patch Location (pre patch)
```
.text:0800B552 40 F2 C5 43                 MOVW    R3, #0x4C5
.text:0800B556 98 45                       CMP     len, R3
.text:0800B558 04 D1                       BNE     loc_800B564
```

Patch Location (post patch)
```
.text:0800B552 40 F2 C5 43                 MOVW    R3, #0x4C5
.text:0800B556 98 45                       CMP     len, R3
.text:0800B558 04 E0                       B       loc_800B564
```

Binary patches:
```
len_based_bug_trigger_5_double_free:
  description: "Do not trigger bug case by making branch unconditional"
  address: 0x800B559
  binfile_offset: 0xB559
  patch_contents: "e0"
```
