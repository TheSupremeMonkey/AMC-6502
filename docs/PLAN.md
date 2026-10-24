# Development and hardware plan

Current priorities are component placement and PCB/case coordination. The software foundation and native schematic draft are working; exact board/case dimensions remain open. See [STATUS](STATUS.md) for actual verification and [DECISIONS](DECISIONS.md) for history.

## Completed milestones

| Milestone | Delivered | Remaining limits |
| --- | --- | --- |
| Local environment | Ubuntu tools, pinned project-local cc65 and `.venv/` Py65 | Keep dependency pins reproducible |
| Machine and banking | NMOS execution, RAM/ROM, four banks, schematic decode, external toggles/reset | Instruction-level timing |
| VIA and serial | Ports, timers, IRQs, PA0 TX/PA1 RX | Shift register and timed handshakes incomplete |
| Terminal/debugger | Run/stop/step, bank-aware breakpoints, registers, safe peeks/edits | Traces/disassembly are future enhancements |
| Firmware/personality | BASIC, Woz, diagnostics, ABI 0.4.0 and Intel HEX loader | Bank 1 reserved; SAVE/downloads pending |
| LCD | Real VIA/I2C/PCF8574/HD44780 mirror/dashboard and terminal inspection | Actual module address/mapping must be verified |
| Hardware draft | Seven-sheet KiCad 9, DIP sockets, single-row headers, exports/ERC | No board layout or electrical bring-up |

## 1. Pre-placement closure and placement feasibility

First close the power/serial review-link design and choose or explicitly reserve the physical controls/displays/connector envelopes. Include four mounting-hole footprints and standoff keepouts in the board study. See [pre-placement audit](SCHEMATIC-AUDIT.md).

Use **110 × 90 mm as the working placement-study envelope**, not final dimensions. The enlarged motherboard may extend below the LCD and use a larger bezel. Keep the LCD-relative four-hole pattern; the old strict 98 × 60 mm motherboard outline is superseded as a fixed constraint.

- [ ] Place all socketed DIP ICs on the LCD-facing top, and three 1×12 buses, the 1×8 mini bus and serial/power connection on the rear-facing bottom.
- [ ] Include oscillator, passives, power circuitry, mounting keepouts and through-hole solder tails; check routing space and actual socket envelopes.
- [ ] Leave a lower front panel for the two bank toggles, reset and power control; decide board-mounted versus wired panel parts and exact footprints.
- [ ] Check LCD backpack/trimmer/header interference and ROM servicing access.
- [ ] Select the board outline only after the trial fits. Present any necessary scope/outline revision before treating it as a requirement.

Acceptance: reviewable placement demonstrates the full BOM, connections and mounting fit in the proposed envelope with usable routing/assembly clearances. Area percentages alone are not proof. See [fit assessment](PCB-FIT.md).

## 2. Printed case and mounting

Accepted shape: mostly upright LCD leaning backward, compact desktop-terminal style; exact angle/base depth remain open. Printed case/back, custom standoffs, brass inserts and four long retaining screws hold the assembly together.

- [ ] Verify the actual LCD outline, hole centers and diameters; 98 × 60 mm / 93 × 55 mm centers are references only.
- [ ] Coordinate angle, base stability, motherboard extension support and front control access.
- [ ] Choose spacer heights from opposing IC/socket/LCD/backpack envelopes and assembly tolerance.
- [ ] Choose screw thread/length and insert locations; check mounting keepouts and supported clamp paths.
- [ ] Locate rear cutouts from final bottom-side connectors, including fully mated DuPont housings/cables, and provide rear-readable signal/power/pin-1 labels.

Acceptance: PCB and case CAD agree on outline, holes, stack, controls, cutouts and assembly/removal. Do not freeze enclosure dimensions before placement. See [mechanical plan](PCB-MECHANICAL.md).

## 3. Close schematic and power details during PCB design

The **1 MHz** target and purchased active oscillator are settled; routine final wiring/bring-up review does not reopen clock-speed selection. Preserve classic MOS parts and all-DIP construction.

- [ ] Resolve USB/source selection, high-side board power switch, off-state serial back-power paths, cable drop, inrush/load and grounding. Draft J15/J16 links remain open until the interface design is complete.
- [ ] Verify cable pin order and current capability; keep the selected FT232RL cable and user-authorized 500 mA assumption distinguished from measured capacity. Retain [power-budget](POWER-BUDGET.md) estimates.
- [ ] Select exact bank digit/common-cathode wiring and segment current; driver/resistor values remain draft.
- [ ] **Verify the actual LCD 7-bit I2C address** and PCF8574 versus PCF8574A/A0–A2 straps. `$27` is only a development default. Confirm mapping, pull-ups and connector order.
- [ ] Route the selected expansion buses and optional removable SD module provision; define shared-rail load limits and preserve unused inputs. SD software is deferred.
- [ ] Complete memory/control/reset wiring review and schematic/ERC checks as design changes; then layout, route and review the board.

Acceptance: explicit netlist and mechanical review, DRC/ERC as applicable, confirmed footprints and a closed power-path design suitable for initial board fabrication.

## 4. Programming and bring-up

- [ ] Use the owned T48 to erase/blank-check/program the complete 64 KB W27C512 image, then read back and compare all bytes.
- [ ] Verify supplies, clock/reset and hardware-bank selection before running serial-only firmware.
- [ ] Run BASIC/Woz/diagnostics on real hardware; verify RAM, VIAs and reset retention.
- [ ] Add the verified-address LCD and check both modes, then test rear expansion connections.

Acceptance: recorded physical measurements, exact fitted parts/firmware hash, reproducible programming steps and observed serial/diagnostic/LCD results.

## Deferred software

Keyboard/profile switch and two-port keyboard ownership; SD driver/card model/filesystem; classic VIA shift-register and timed handshakes; downloads/BASIC storage; further debugger tools. Implement these only when needed, using modeled hardware interfaces and bounded tests. Preserve existing firmware ABI addresses and RAM reservations in [MACHINE](MACHINE.md) and [FIRMWARE-API](FIRMWARE-API.md).

## Optional extra RAM — deferred

Current decode provides six spare 2 KB slots at `$8000–$AFFF`; no extra RAM is fitted/emulated. The optional future population could add up to 12 KB under this map. The earlier 47 KB/two-decoder proposal is not selected. See [RAM-EXPANSION.md](RAM-EXPANSION.md).

Implemented selector revision: one LS138 provides eight 2 KB slots, VIAs on Y6/Y7 (`$B000`/`$B800`), and existing LS00 gate D selects ROM. Retain LS21 RAM-write qualification. Validate physical pin polarities and native logic truth table before placement; current spare selects are available at internal J2. See [ADDRESS-DECODING.md](ADDRESS-DECODING.md).

- [ ] **After user inventory check (planned 2026-10-25):** record any 6116 markings, quantity and DIP package dimensions. Decide fitted RAM versus empty upgrade sockets, socket count and placement allowance. Baseline remains 32 KB and no sockets are added pending that choice. See [RAM-EXPANSION.md](RAM-EXPANSION.md).
