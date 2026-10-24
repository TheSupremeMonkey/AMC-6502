# Shared 8 KB firmware concept

Status: proposal for discussion, 2026-10-23. This describes a target design, not completed features or a frozen ABI. Current implementation is documented in [FIRMWARE.md](FIRMWARE.md).

## Purpose

The upper ROM at `$E000–$FFFF` provides a small BIOS for every personality. BASIC, Woz Monitor, diagnostics, and a future standalone shell live in their lower 8 KB payloads. They call shared services rather than each implementing device drivers. Keep classic NMOS 6502 compatibility and the 1 MHz baseline.

All upper-ROM bytes remain mirrored except the 32-byte bank description at `$FFC0–$FFDF`. CPU vectors at `$FFFA–$FFFF` remain shared.

## Startup experience

1. Mask interrupts, initialize CPU execution state and kernel-owned workspace.
2. Install safe IRQ/NMI defaults; initialize only system-owned VIA resources.
3. Initialize serial; optionally initialize the LCD/keyboard when configured.
4. Print the retro banner and current bank description. Report configured devices without inventing successful self-test results.
5. Enter the active personality at `$C000`. Boot BASIC directly in bank 0; do not require an extra menu before its prompt.

Full RAM/peripheral diagnostics remain an explicit bank 3 operation. Avoid destructive POST scans on every reset. Physical RAM retention does not imply a running session can resume after reset.

## Shared services

| Service | Target behavior | Current state |
| --- | --- | --- |
| Boot and bank identification | Reset, banner, description, payload entry | Implemented foundation |
| Console output/input | Stable character calls, CR/LF, serial/LCD routing | Serial character calls implemented |
| Console helpers | Strings, hex formatting, editable line input, polled input/status | Implemented for serial; see [API](FIRMWARE-API.md) |
| Bank management | Read bank, select/reset, restart current bank | Selector and select/reset vector implemented |
| VIA support | Initialize owned resources, safe timer helpers, interrupt dispatch | Device model and IRQ hook implemented; common helpers proposed |
| Time services | Optional system tick, delay, elapsed-time queries | Proposed; not enabled automatically |
| LCD/I2C | Character output, cursor/clear, bank/status dashboard | Proposed |
| Keyboard | Matrix scan, debounce, character translation, console input | Proposed; exact matrix still undecided |
| Program transfer | Checked serial upload/download of permitted user RAM | Proposed; protocol undecided |
| Error handling | Service status codes, safe interrupt defaults, optional break hooks | Partial defaults; full policy proposed |

The accepted [operating-profile plan](OPERATING-PROFILES.md) distinguishes Cyberdeck (keyboard/LCD, two keyboard ports) from Controller (serial, keyboard ports available to the application). Selection is sampled at reset; LCD availability remains independent. Profile implementation and selector wiring are deferred.

Console routing should be explicit: terminal, standalone keyboard/LCD, or optional mirrored output. Bank descriptions can populate both terminal banner and LCD. Applications need not know how LCD backpack bits are wired.

## Stable call interface

Retain the existing three-byte JMP entries:

| Address | Existing service | Contract |
| --- | --- | --- |
| `$E100` | COUT | A = ASCII character; preserves A/X/Y |
| `$E103` | CIN | Blocking input; returns character in A, preserves X/Y |
| `$E106` | BANK_SELECT | A = bank 0–3; valid calls reset and never return; invalid calls return carry set |

String/hex output, line editing, polling, version, bank query, and CR/LF entries are now appended through `$E121`; their implemented contracts and RAM ownership are in [FIRMWARE-API.md](FIRMWARE-API.md). Append future entries rather than moving these addresses. Proposed additions include input polling, string/hex/line helpers, bank query, LCD operations, keyboard polling, timer/time queries, and program transfer. Define register use, carry/status results, scratch memory, interrupt safety, and reentrancy for each service before implementation. Version the ABI so applications can query available services.

Keep indirect IRQ hook `$02F2–$02F3` compatible. A default handler must handle or disable unexpected enabled sources safely rather than permit an endless unacknowledged IRQ loop. Define how kernel-owned timer sources and application handlers share dispatch before enabling background services. NMI/BRK policies require explicit design; an emulator debugger is a separate host feature.

## ROM organization

| Region | Role |
| --- | --- |
| `$E000` onward | Kernel entry/header and future capability information |
| `$E100` onward | Stable JMP service table |
| Remaining code space below `$FFC0` | Drivers, startup/banner, helpers, dispatch, transfer routines, shared tables |
| `$FFC0–$FFDF` | Per-bank description; sole mirroring exception |
| `$FFE0–$FFF9` | Reserved until deliberately allocated |
| `$FFFA–$FFFF` | NMI, RESET, IRQ/BRK vectors |

Current serial routines and banner occupy linker-assigned sections beginning at `$E200` and `$E400`. Other internal placements may change; clients call the stable table. Use linker bounds and generated maps to measure capacity. This feature list is a proposed 8 KB target, not proof that every eventual implementation fits. Keep headroom and measure as services are added.

## RAM and resource ownership

Firmware needs writable state even though code is in ROM. Specify a common RAM map for zero-page pointers, IRQ hooks, serial scratch, console input, keyboard state, and optional tick counters. Existing console/hook scratch uses `$02F0–$02F3`; diagnostics also uses `$00–$05` and `$02F4–$02F8`, and Woz uses `$0200–$027F` plus its zero-page variables.

Do not place new buffers where BASIC's allocator can overwrite them. Any additional reserved RAM must be reflected in BASIC's RAM limit, linker configurations, diagnostics exclusions, and loader bounds. Exact expanded workspace allocation remains open. Drivers should not silently reconfigure expansion ports or timers owned by an application.

## Practical limits and boundaries

- Serial is software-driven at 1 MHz. Background timers/keyboard IRQs must not corrupt bit timing. Interrupt masking, cooperative polling, resource ownership, and any buffering need tests before combining them; reliable asynchronous input is not already available.
- Ctrl-C in BASIC requires an interpreter break-check integration. Shared firmware cannot guarantee interruption of arbitrary machine code that never polls or masks interrupts. Host debugger stop/step controls are separate.
- The LCD can show bank identity and deliberately collected status. It cannot continuously read internal CPU registers by itself.
- A serial program-transfer service can precede a storage design. It does not imply a disk filesystem or completed BASIC LOAD/SAVE integration. Choose a protocol and host-side support explicitly.
- Full BASIC, Woz command parsing, and diagnostics stay in payloads. Do not duplicate their interpreters in shared firmware. BASIC-specific language changes remain in its port.
- The provisional `$8020` selector still requires physical decode/latch/reset circuitry. Firmware layout does not complete hardware design.

## Suggested implementation order

1. Define the service ABI, workspace/resource ownership, and safe IRQ dispatch.
2. Add shared formatting, input-status, and line-editing services with firmware tests.
3. Add LCD/I2C drivers and emulator model, then keyboard support once its matrix is specified.
4. Add optional tick services after verifying coexistence with software serial.
5. Add checked program transfer and integrate BASIC storage hooks if desired.

Acceptance for the completed core: all personalities boot through common startup; use stable console/bank interfaces; serial and configured standalone I/O work; interrupt/resource ownership is tested; loaders respect memory boundaries; diagnostics and fault tests pass; and the final shared build fits in 8 KB with only the declared metadata varying between banks.

Serial RAM upload is implemented through `FW_LOAD`; see [Serial loader](SERIAL-LOADER.md). It accepts checksummed Intel HEX records of up to 16 data bytes, writes only `$0300–$7FFF`, and never launches automatically. Downloads and BASIC save/restore remain pending.
