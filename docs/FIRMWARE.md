# Banked test ROM and upstream sources

For stable service calls and workspace ownership, see [FIRMWARE-API.md](FIRMWARE-API.md). For all ways to change personalities, see [Changing ROM banks](ROM-SWITCHING.md).

## Build and run

```sh
make setup
make rom
make test
make run
```

`make rom` validates/fetches pinned sources into ignored `.tools/` directories and builds `build/amc6502.bin`, an exact 65,536-byte EEPROM image. First download requires network access. Subsequent builds validate and reuse clean checkouts; unexpected revisions or local changes are rejected rather than overwritten. `make setup` prepares the assembler and Python environment; `make rom` fetches firmware separately.

The build stages upstream source into `build/` and applies the AMC-specific changes there. Original checkouts are not modified. Listings, label files, maps, intermediate binaries, source provenance, and upstream notices are retained in `build/`.

## Image layout

| Bank | EEPROM offsets | CPU payload `$C000–$DFFF` | CPU shared `$E000–$FFFF` |
| --- | --- | --- | --- |
| 0 | `$0000–$3FFF` | Microsoft BASIC, OSI configuration | Identical kernel |
| 1 | `$4000–$7FFF` | Reserved: idle loop | Identical kernel |
| 2 | `$8000–$BFFF` | Woz Monitor | Identical kernel |
| 3 | `$C000–$FFFF` | Hardware diagnostics | Identical kernel |

The shared reset handler initializes stack, decimal/IRQ state, and serial pins, prints the AstroMonkey ASCII rocket boot banner, then jumps to `$C000`. The common banner includes a bank-specific description and announces the configured machine; it does not claim to have passed diagnostics. Bank payloads provide their own entry there. The selector survives CPU and VIA reset. The button advances `0 → 1 → 2 → 3 → 0`; RAM survives, but the CPU, VIA port state, queued serial input, captured output, and cycle epoch reset. Reset does not preserve a suspended BASIC/monitor session. BASIC initialization may subsequently overwrite retained RAM.

The sole upper-half mirroring exception is `$FFC0–$FFDF`: a 32-byte ASCII bank description, zero-padded with at least one null terminator. The linker reserves it and the image builder fills it for each bank. Shared banner code reads the active ROM directly, so no selector register or host-side banner substitution is needed. IRQ/reset vectors and every byte outside this field remain identical. `:status` also shows the selected bank.

## Terminal use

`make run` starts bank 0. Press Enter at `MEMORY SIZE?` to probe available RAM, then Enter at `TERMINAL WIDTH?` to accept the default. Try:

```text
PRINT 2+2
10 PRINT "AMC BASIC"
20 END
RUN
```

Host commands (not firmware instructions):

- `:bank 3`: simulate holding reset and setting bank 2 for Woz Monitor. An explicit choice is required.
- `:bank 1` through `:bank 4`: directly select banks 0–3 and reset, from any personality.
- `:reset`: reset the currently selected bank.
- `:continue`: run another bounded slice without sending firmware input.
- `:status`: show selected bank, CPU PC, and emulated instruction cycles.
- `:quit`: exit; EOF also exits. Ctrl-C pauses the emulator without resetting it.

In Woz Monitor, try `0300: AB`, then `0300` on the next line to store and inspect a RAM byte. `C000` examines the active payload; `E000` examines the common kernel. Two more button presses return from bank 2 to BASIC through diagnostics bank 3 (which runs only when execution resumes in that bank).

The terminal accepts ASCII lines and defaults to bounded 1,000,000-instruction slices for startup and firmware input. Use `:run` for continuous execution, `:stop` or Ctrl-C to pause, and `:continue` for another bounded slice. Registers, stepping, breakpoints, and memory inspection/editing are host debugger features; see [DEBUGGER.md](DEBUGGER.md). Firmware break scanning remains unimplemented. Serial input is intentionally paced, and legacy firmware input-buffer limits still apply. Host terminal line echo may appear in addition to firmware echo.

## Console model and ABI

The original common entries remain `$E100` = character output, `$E103` = blocking character input, and `$E106` = bank select/reset (A=0–3). Additional helpers occupy `$E109–$E121`; see [FIRMWARE-API.md](FIRMWARE-API.md) and `firmware/include/fw.inc`. The console routines preserve X/Y; output also preserves A. Console output masks bit 7 for historical BASIC string markers, so this ABI is ASCII rather than binary-transparent. Kernel services reserve ZP `$F0–$F1`, line buffer `$0280–$02EF`, serial scratch `$02F0–$02F1`, IRQ hook `$02F2–$02F3`, and line state `$02F9–$02FB`; BASIC uses RAM from `$0300` upward and its upstream zero-page layout; Woz uses `$24–$2B` and `$0200–$027F`.

Firmware bit-bangs 8N1 serial through VIA #1 PA0 (TX) and PA1 (RX), using ORA `$8001` and DDRA `$8003`. The peer schedules RX bits and samples TX bits in emulated cycles, at 104 cycles/bit (approximately 9600 baud at 1 MHz). Tests exercise actual firmware drivers; no CPU-PC traps or emulator console calls are used. Instruction-level timing approximates access within an instruction. Firmware delays match the fixed 1 MHz hardware target; higher-clock timing is outside current scope.

Both VIAs now model ports, Timer 1/2, control-input interrupts, and IFR/IER; see [VIA.md](VIA.md). Shift-register operation and timed output handshakes are not implemented. Reserved/unmapped I/O reads `$FF` and ignores writes. LCD console/dashboard support is implemented. The shared kernel initializes a RAM IRQ hook to a default RTI handler on reset. BASIC/Woz keep interrupts masked; bank 3 installs a real acknowledging handler for its timer checks. See [DIAGNOSTICS.md](DIAGNOSTICS.md) for workspace and behavior. This change does not add background interrupts to BASIC/Woz or establish physical timing compatibility.

## Upstream source provenance

All revisions are pinned in `scripts/fetch_firmware.py`.

- [Microsoft BASIC-M6502](https://github.com/microsoft/BASIC-M6502), commit `7460af2c03ae19c0e60ff327489229d2005b9357`: official historical BASIC V1.1 source, MIT license, copyright Microsoft Corporation. Downloaded for reference and provenance. Its period assembler syntax is **not** what the current ca65 build assembles.
- [Michael Steil's msbasic](https://github.com/mist64/msbasic), commit `2a0bc2fe0db13f8cf1b5c40b1d5617263cdb9cb4`: ca65-compatible combined Microsoft BASIC source, upstream README declares 2-clause BSD. Credits include Michael Steil and contributors, with names/comments from Bob Sander-Cederlof's disassembly. The AMC build uses the OSI configuration (six-digit floating point, historical OSI V1.0 Rev 3.2 banner), relocated to `$C000`. It is Microsoft BASIC lineage, not a claim to assemble the official V1.1 release verbatim. The build adds a cold-start entry, asserts BASIC workspace stays clear of kernel allocations, redirects console calls, disables the unimplemented break scanner, and makes unsupported LOAD/SAVE report syntax errors. Ctrl-C handling and storage are not implemented.
- [Jeff Tranter's Woz Monitor source](https://github.com/jefftranter/6502/tree/master/asm/wozmon), commit `0d20e5964544ccd8386ca21e562b49cb6b6a64d0`: original Woz Monitor by Steve Wozniak (1976), ca65 version. Upstream distinguishes its author's Apache-2.0 code from ports of historical software; the original Woz source has attribution but no separate explicit license in this directory. Do not describe the original monitor as Apache-licensed merely because of the repository README. The build relocates it to `$C000`, removes Apple-1 PIA setup/vectors, and routes input/output through shared serial routines while preserving its high-bit ASCII parser.

Preserve upstream attribution and notices when sharing sources or images. The build places source notes and downloaded upstream notices beside the ROM; it does not assign a new license to historical sources.

## Verification

Integration tests check the exact image size and four upper halves identical except for bank descriptions; boot BASIC; answer its initialization prompts; run arithmetic and a stored program; verify unsupported LOAD reports an error; cycle through reserved bank 1 into Woz Monitor; store/read RAM there; and cycle back into a fresh BASIC boot. Tests also check VIA direction/reset behavior and ROM write protection at both halves' boundaries. Legacy 8 KB diagnostic fixtures remain supported explicitly for regression tests; they do not represent the current banked target layout.


## Bank 3 diagnostics

`:bank 4` selects bank 3. It automatically checks RAM and both timers/IRQ on both VIAs, prints PASS/FAIL, and accepts `R` to rerun. `:bank 1` returns to BASIC. See [DIAGNOSTICS.md](DIAGNOSTICS.md) for preservation limits and test coverage. Bank 1 is the only remaining placeholder.


## Retro boot banner

Every power-on, bank change, or host reset prints the shared ASCII rocket, `A M C - 6 5 0 2`, `ASTROMONKEY MICRO COMPUTER`, `SYSTEM ROM 0.1`, the configured memory/bank sizes, and `READY FOR LAUNCH`. It uses real shared firmware serial output rather than host terminal decoration. Banner code/data lives at `$E400` onward, separate from timing-sensitive console loops. The reset banner precedes each personality's prompt, including reserved bank 1. Diagnostic `R` reruns do not reset and therefore do not repeat the boot banner. Terminal execution slices are now 1,000,000 instructions to leave room for both the banner and the diagnostic report before accepting input.


## Bank descriptions

The banner appends one of these lines after the shared rocket text:

```text
BANK 0: MICROSOFT BASIC
BANK 1: RESERVED
BANK 2: WOZ MONITOR
BANK 3: HARDWARE DIAGNOSTICS
```

Records are configured in `scripts/build_rom.py`; the reader is bounded to 32 bytes even if a terminator is absent. The builder rejects descriptions too long for a terminator. Tests verify record content/padding, identical firmware and vectors outside the record, and correct output on every bank reset. The earlier proposed `$FFE0–$FFEF` metadata layout is superseded.


## Manual bank controls

See [ROM switching](ROM-SWITCHING.md). Software bank selection is retired: `$8020` is unpopulated expansion and `$E106` returns carry set. Numeric diagnostic keys do not switch ROMs. Host `:bank 1..4` represents toggles and reset.

Serial RAM upload is implemented through `FW_LOAD`; see [Serial loader](SERIAL-LOADER.md). It accepts checksummed Intel HEX records of up to 16 data bytes, writes only `$0300–$7F7F`, and never launches automatically. Downloads and BASIC save/restore remain pending.

## Physical programming equipment

User-owned programmer: **XGecu T48 (TL866-3G)**. Published device list includes W27C512 DIP28. Plan erase/blank-check, load `build/amc6502.bin` at image offset zero, program and verify the entire 64 KB device, with placement/device algorithm from the programmer software. Hardware flashing/readback has not been performed; see [BOM](BOM.md).

Current schematic migration (2026-10-23): VIA1 `$B000–$B7FF`, VIA2 `$B800–$BFFF`, repeated 16-register aliases; PA0 TX/PA1 RX. Manual bank toggles plus reset replace software selection. `$E106` returns carry set; `$8020` is unpopulated expansion. See [ROM switching](ROM-SWITCHING.md). LCD mirror/dashboard support is implemented; see [LCD guide](LCD.md).

LCD mirror/dashboard drivers are now in shared ROM, API 0.4.0. `:lcd mirror/dashboard/off` requests modes; `:lcd` inspects the display. The top 128 RAM bytes and ZP `$F2–$F3` are LCD-owned; BASIC and uploads end at `$7F7F`. See [LCD.md](LCD.md), including the required actual-address verification.

## Shared 8 KB ROM usage

Measured from the current verified build's `build/kernel.map` (reviewed 2026-10-24):

| Segment | Allocated bytes |
| --- | ---: |
| Reset entry (`KERNEL`) | 3 |
| Public jump table (`ABI`) | 45 |
| Reset/serial/console glue (`DRIVERS`) | 308 |
| Boot banner/code (`BOOT`) | 224 |
| Console helpers and HEX loader (`SERVICES`) | 617 |
| LCD/I2C firmware (`LCD`) | 939 |
| Per-bank description (`BANK_INFO`) | 32 |
| CPU vectors | 6 |
| **Total occupied/reserved** | **2,174 / 8,192 (26.5%)** |

**6,018 bytes remain unallocated** (73.5%). This is segment allocation, not a count of non-`$FF` bytes: the binary is always padded to the full 8 KB. Of the free space, **4,117 bytes at `$EFAB–$FFBF`** form a contiguous gap before metadata; the remaining 1,901 bytes are gaps between fixed segments and near the top vectors. Fixed-start segments may need to be moved/extended to use all gaps; public vector addresses must stay stable. Code/data/vectors occupy 2,142 identical bytes per bank, plus the 32-byte bank-specific metadata reservation.
