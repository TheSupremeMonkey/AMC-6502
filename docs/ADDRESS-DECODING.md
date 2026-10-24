# Address decoding: eight 2 KB slots

Accepted/implemented: 2026-10-24. This replaces the former 4 KB upper-space decoder layout. Keep the existing 32 KB RAM and four 16 KB ROM banks. Optional extra RAM is **not fitted or emulated**.

## Memory map

| LS138 output | CPU range | Allocation |
| --- | --- | --- |
| — | `$0000–$7FFF` | Existing 32 KB HM62256 RAM |
| Y0, pin 15 | `$8000–$87FF` | Unpopulated expansion slot 0 |
| Y1, pin 14 | `$8800–$8FFF` | Unpopulated expansion slot 1 |
| Y2, pin 13 | `$9000–$97FF` | Unpopulated expansion slot 2 |
| Y3, pin 12 | `$9800–$9FFF` | Unpopulated expansion slot 3 |
| Y4, pin 11 | `$A000–$A7FF` | Unpopulated expansion slot 4 |
| Y5, pin 10 | `$A800–$AFFF` | Unpopulated expansion slot 5 |
| Y6, pin 9 | `$B000–$B7FF` | VIA1; registers repeat every 16 bytes |
| Y7, pin 7 | `$B800–$BFFF` | VIA2; registers repeat every 16 bytes |
| — | `$C000–$FFFF` | Selected 16 KB ROM bank: 8 KB personality + 8 KB shared firmware |

There are eight logical decode windows, **not eight newly designed physical card connectors**. Six windows remain available (12 KB). Unpopulated emulator reads return `$FF`; writes are ignored. Each VIA has 128 aliases of its 16 registers in its 2 KB window. `$8020` is now an unpopulated expansion address, not a VIA alias or bank register.

## Corrected package wiring

The user-supplied concept is used with two important corrections: active-low SRAM `/CE` connects **directly to A15**, and the LS138 has **pin 8 ground / pin 7 Y7**. Inverting A15 before this SRAM's active-low enable would incorrectly select RAM in upper memory. For a hypothetical active-high RAM enable, the required polarity would instead be NOT A15; that is not our fitted HM62256.

U4 74LS138:

| Pin | Connection |
| --- | --- |
| 1 / A | CPU A11 |
| 2 / B | CPU A12 |
| 3 / C | CPU A13 |
| 4 / active-low G2A | CPU A14 |
| 5 / active-low G2B | Ground |
| 6 / active-high G1 | CPU A15 |
| 8 / GND | Ground |
| 16 / VCC | +5 V |

It is enabled only when A15=1 and A14=0, covering `$8000–$BFFF`. Output pins and windows are in the map above. VIA CS1 remains high; its active-low CS2 receives the appropriate output. [TI LS138 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls138.pdf) is the pinout/function reference.

U6 74LS00 gate D pins **12=A15, 13=A14, 11=ROM_CE_N**. This selects ROM only when both address bits are high. U2 RAM `/CE` stays on A15. U6 gate A keeps READ_N=NOT(R/W); ROM/RAM output enable is low only for reads.

## Address selection versus write-control circuitry

The LS138 and LS00 provide the requested address selection. The existing **74LS21 is retained for reset-qualified write control**, and the HC14 is retained for reset. The whole board therefore still has those additional logic packages; no claim of only two total logic ICs is made.

- U5 gate B: WRITE_OK = PHI2 AND READ_N AND RESET_N (fourth input tied high).
- U6 gate B: RAM_WE_N = NOT(WRITE_OK), by tying both inputs together.
- U5 gate A and U6 gate C are unused: inputs tied low, outputs unconnected.

Preserving these controls avoids removing established reset/write protection just to meet a two-package address-selector headline. RAM write qualification remains separate from chip selection. No additional RAM, decoder, clock divider or bank selector is added.

## Expansion and software

J2 is expanded to a 1×8 **internal decode/test header**: pins 1–6 expose EXP0_N–EXP5_N, pin 7 GND, pin 8 +5 V. It does not include CPU address/data/RW/clock and is not a complete memory-expansion bus. Existing rear VIA expansion headers, mini bus and serial interface keep their functions and pin numbers.

Firmware `hardware.inc` defines VIA1 `$B000` and VIA2 `$B800`; Python `memory_map.py` defines the matching model constants. Console, LCD, diagnostics, IRQ fixture and tests migrate together. ROM banking, public firmware API 0.4.0, RAM workspace and metadata layout are unchanged. Rebuild the ROM: prior hardware-map images do not match the new VIA addresses.

Optional RAM may later occupy some or all of the six spare slots, with appropriate chip enables and no I/O overlap. That would require a separate schematic/software change, including deciding whether to move the LCD workspace so BASIC can use a larger contiguous region. See [RAM-EXPANSION.md](RAM-EXPANSION.md).

## Verification

`make schematic-check` exports native KiCad netlist/PDF, runs ERC, verifies 26 key physical-pin connections and evaluates the exported LS138/LS00/LS21 logic for 256 address/control combinations. Checks cover non-overlapping RAM/ROM/VIA selection, all spare selects, read enable and reset/PHI2-qualified writes. This is static logical checking, not physical signal timing or bring-up.

Emulator tests also check all 65,536 CPU addresses, slot/device boundary writes, independent aliased IRQ acknowledgement, real BASIC/Woz/diagnostics and LCD/serial upload behavior.
