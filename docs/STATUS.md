# Current status

Last reconciled: 2026-10-24. Accepted requirements, implemented behavior and open choices are separated below. Historical alternatives remain in [DECISIONS](DECISIONS.md).

## Working software

- Terminal emulator uses Py65 NMOS 6502; ca65 targets classic 6502 at nominal 1 MHz. The eight-2-KB-slot schematic map is implemented: RAM `$0000–$7FFF`, mirrored VIA blocks `$B000`/`$B800`, expansion `$8000–$AFFF`, four 16 KB ROM banks `$C000–$FFFF`.
- ROM banks: BASIC, reserved, Woz Monitor and diagnostics. Upper 8 KB is shared except metadata `$FFC0–$FFDF`; every reset prints the rocket/banner and personality.
- External toggle positions select ROM; reset retains selection and RAM. Host `:bank 1..4` combines toggles/reset; `--bank 0..3` chooses initial positions. No software selector; `$8020` is an unpopulated expansion address and `$E106` returns unsupported.
- Firmware API 0.4.0 includes serial on PA0 TX/PA1 RX, string/hex output, edited input, idle-nonblocking polling, queries and checksummed Intel HEX RAM upload. Debugger supports run/stop/step, bank-aware breakpoints and side-effect-free inspection.
- LCD mirror/dashboard modes drive real modeled VIA PA2/PA3 I2C, PCF8574 and HD44780 signals. `:lcd` inspects; `:lcd mirror/dashboard/off` requests modes. Dashboard diagnostics updates the status row on rerun. Validated retained RAM preserves mode through warm bank resets.
- LCD owns ZP `$F2–$F3`, `$02FD` request mailbox and `$7F80–$7FFF`; BASIC, loader and restoring diagnostics use user RAM only through `$7F7F`. See [MACHINE](MACHINE.md) and [LCD](LCD.md).

## Hardware and mechanical direction

All ICs are DIP with sockets. Selected inventory: original MOS 6502 (0284), two original MOS 6522s, HM62256ALP-10 100 ns, W27C512-45Z, owned 74HC14 and capacitors. Clock is settled at 1 MHz using the purchased active oscillator, assumed 5 V/half-size DIP8. Address selection uses LS138/LS00; LS21 remains for reset-qualified writes. T48 programmer is owned.

Native seven-sheet KiCad 9 schematic is available. Three 1×12 and one 1×8 standard 2.54 mm male headers are selected. Mini bus is PA4–PA7 plus CA1/CA2, power/ground; full ports are VIA1 PB, VIA2 PA and VIA2 PB with associated controls. Actual bottom-side placement has not been performed.

The current case concept is **mostly upright and leaning backward**, with bank toggles/reset/power below the LCD. Printed case, custom standoffs, brass inserts and four long retaining screws remain the direction. ICs face the LCD; all three full-port buses, mini bus and serial/power connection face rear-cover cutouts. A larger motherboard/bezel is allowed, particularly below the display, while retaining the LCD-relative hole pattern.

**110 × 90 mm is the working placement-study envelope; final size is not frozen.** Reference LCD is 98 × 60 mm, with 93 × 55 mm hole spacing, pending actual-module verification. The ten DIP/socket courtyards consume about 89% of the old 98 × 60 mm board, versus 53% of 110 × 90 mm. These are area estimates, not a completed placement/routing proof. See [PCB fit](PCB-FIT.md) and [mechanical plan](PCB-MECHANICAL.md).

No PCB layout, enclosure CAD, physical programming or board operation is complete. Panel versus board-mounted control parts remain open; their location below the LCD is settled.

## Verification already run

- `make test`: **76 tests passed** after rebuilding for the eight-2-KB-slot map. Includes an exhaustive 65,536-address model check, slot boundary writes, aliased IRQ acknowledgement, BASIC/Woz/diagnostics, serial polling and all LCD/loader regressions.
- ROM SHA-256: `57990e1b8f44515a6994109df74ea4842187bcb92f3d73e76485e1e03c1d005d`. Firmware allocation remains 2,174 of 8,192 shared bytes; only MMIO addresses change, not the public API 0.4.0 layout.
- `make schematic-check`: KiCad 9.0.8 reports **zero ERC violations**, exports PDF/netlist, checks **26 key pins** and evaluates **256 native-netlist address/control combinations**. Decode sheet rendered and visually reviewed.
- No physical flash/board operation is claimed. Current proof is assembled firmware, instruction-level emulation and static native schematic checks. Earlier generated transcripts/hashes are historical; rebuild before programming a new map.

## Next actions

1. Close or explicitly reserve the unresolved power/serial circuitry and physical control/display envelopes, then trial-place the complete socketed-DIP BOM and rear headers in the working larger envelope. Preserve LCD-relative holes, leave control-panel space, and check routing/mounting/component clearance before choosing final size.
2. Coordinate upright tilt, base depth/stability, LCD backpack clearance, lower-board support, mated DuPont housings, spacers/inserts/screws and rear cutouts with the printed case.
3. Select exact control footprints/mounting and optional bank digit. Finish the deferred PCB power/source/switch/USB off-state-isolation design; J15/J16 serial links remain unresolved in the draft.
4. Verify actual LCD outline/holes, **I2C address** (development `$27`) and backpack mapping/pull-ups. Confirm cable pin order/current capability and physical parts' condition, then finish board review and program/read back the ROM before bring-up.

SD, keyboard/profile implementation, VIA shift-register/timed handshakes, downloads/BASIC storage and firmware break scanning remain deferred. Emulator timing is instruction-level; serial/LCD services are synchronous and have no background UART receiver. More precise physical/bus-cycle behavior is not claimed.

Pre-placement audit (2026-10-24): core CPU/memory/VIA/reset/decode parts are represented. Main closure items are power/serial (J15/J16 review links), exact physical controls/displays, and PCB mounting-hole/keepout geometry. `make schematic-check` rerun: zero ERC violations and 26 key connections pass. See [SCHEMATIC-AUDIT.md](SCHEMATIC-AUDIT.md). No added component choice or completed electrical sign-off is implied.

Shared firmware allocation from the verified linker map: **2,174/8,192 bytes (26.5%)**, leaving 6,018 unallocated. The largest contiguous gap is 4,117 bytes at `$EFAB–$FFBF`; other free bytes lie between fixed segments. LCD/I2C code uses 939 bytes. See [FIRMWARE.md](FIRMWARE.md).


Current decoder revision: VIA1 `$B000–$B7FF`, VIA2 `$B800–$BFFF`, six unpopulated 2 KB slots `$8000–$AFFF`. RAM remains 32 KB; optional extra RAM is deferred. Corrected supplied wiring: RAM `/CE` = A15 directly; LS138 pin 8 ground, pin 7 Y7. ROM select uses LS00 gate D; existing LS21 write/reset qualification retained. Schematic/source/tests/docs migrated together; see [ADDRESS-DECODING.md](ADDRESS-DECODING.md).

Optional RAM follow-up: user plans an inventory check on 2026-10-25 for 6116 parts, then may choose populated RAM or empty upgrade sockets. No added socket count, footprint or RAM-limit change is committed. Baseline remains 32 KB; six spare 2 KB slots are available. See [RAM-EXPANSION.md](RAM-EXPANSION.md).
