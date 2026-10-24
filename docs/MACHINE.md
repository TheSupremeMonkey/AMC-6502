# Machine contract

This is the working emulator specification. It describes implemented behavior against the current schematic draft; physical validation and PCB/case choices are tracked separately.

Original/classic chip behavior is the baseline. The current board is fixed at 1 MHz; modern CPU variants remain a separate experimental option. Baseline firmware remains NMOS-compatible; any variant-specific core, instructions, or behavior must be explicitly configured and tested. No modern-variant emulator configuration exists yet. The 1 MHz target and selected parts are settled; physical condition and remaining implementation details are tracked in BOM.md.

## Implemented schematic map

| CPU range | Device |
| --- | --- |
| `$0000–$7FFF` | 32 KB RAM |
| `$8000–$AFFF` | Six unpopulated 2 KB slots; reads `$FF`, writes ignored |
| `$B000–$B7FF` | VIA1, register selected by A0–A3 |
| `$B800–$BFFF` | VIA2, register selected by A0–A3 |
| `$C000–$FFFF` | One of four 16 KB ROM banks |

Each VIA's 16 registers repeats 128 times throughout its 2 KB block. `$8010` and `$8020` are unpopulated expansion addresses; no bank register exists. Four banks retain the 8 KB personality / 8 KB shared-kernel layout. Only metadata `$FFC0–$FFDF` differs between upper halves. CPU remains Py65 NMOS 6502, terminal only, deterministic cycle accounting at nominal 1 MHz.

## Fixed clock

The user locked the current hardware target to **1 MHz** and purchased a **1 MHz active oscillator module**. Assume the **5 V** version by explicit instruction and use the supplied ECS-2100 half-size DIP-8/four-lead mechanical/pinout reference. Exact manufacturer/model is unspecified; the reference does not prove ECS manufacture. No separate crystal, oscillator amplifier, feedback/load network, divider, or speed-selection jumper is part of this board. Local bypassing and clock/reset distribution are still needed. See [BOM](BOM.md) for the retained reference sheet and design assumptions.

This supersedes former selectable-speed and later bare-crystal/divider alternatives. Plan reset around the reference sheet's startup interval and the CPU/VIA requirements.

Firmware serial delays and serial-peer timing already target this nominal clock. The emulator advances deterministic CPU cycles independently of host speed; execution is not wall-clock throttled. No firmware or emulator frequency migration is required for this decision. Modern CPU substitution remains a separate experiment, not a reason to add clock-selection hardware.

## Reset and bank selection

Two external toggle positions supply EEPROM A14/A15. `Machine(rom, bank=n)` models initial positions; default is bank 0. `set_bank_switches(n)` changes ROM mapping immediately without resetting CPU/peripherals. As on hardware, changing switches while code runs is unsafe. Normal `select_bank(n)` / terminal `:bank 1..4` simulate holding reset, setting switches and releasing reset. There is no cycling button or software selection.

Reset retains switch selection and RAM, resets both VIAs/serial peer and cycle epoch, and fetches the selected ROM's reset vector. RAM starts deterministically zeroed for reproducible tests; physical power-on contents are unspecified. IRQ-disable is set explicitly. Reset waveform, oscillator startup and individual bus cycles are outside this instruction-level model.

## Fidelity

Begin with instruction-level CPU execution and cycle accounting. This is a firmware-development tool, not yet a bus-cycle-accurate hardware simulator. Verify and document relevant classic NMOS 6502 instructions, interrupts, decimal behavior, undocumented-opcode policy, and timing differences before firmware relies on them.

Serial and LCD firmware should drive modeled VIA pins. Their device models should consume those signals rather than replacing firmware drivers with emulator-specific output calls. Specify timing limits as implementation progresses.

## Implemented firmware and peripherals

Shared reset prints the rocket/banner and ROM metadata, then enters `$C000`. Bank 0 is MS BASIC, bank 1 idle, bank 2 Woz Monitor and bank 3 diagnostics. Both VIAs implement ports/directions, timers, control-input edges and IRQ; see [VIA.md](VIA.md). IRQ requests combine onto the CPU IRQ line. Serial is PA0 TX / PA1 RX, idle-high 8N1 at approximately 9600 baud. Firmware preserves other Port A output latch bits via `FW_PORTA_SHADOW` at `$02FC`; all future output writers must update this shared shadow and preserve unrelated direction bits.

PA2/PA3 remain reserved for I2C, PA4–PA7 for the mini bus. LCD mirror/dashboard modes and a write-side PCF8574/HD44780 model are implemented. Keyboard, SD, shift-register operation and timed output handshakes remain unimplemented. Unclaimed pins remain inputs. Unmapped expansion reads use deterministic `$FF`, not an analog floating-bus model. ROM writes are ignored.

The `$E106` service slot is retired: returns C=1 without selecting/resetting. `FW_BANK_GET` reads the digit in the active ROM's `BANK n:` metadata, not imaginary selector hardware. Firmware ABI is 0.4.0. Numeric diagnostic keys no longer change banks. See [ROM-SWITCHING.md](ROM-SWITCHING.md).

Legacy 8 KB regression fixtures remain explicitly supported at `$E000–$FFFF` without VIAs or banking. They are test fixtures, not an alternate board map.

## Planned operating profiles

Plan a reset-sampled mechanical Cyberdeck/Controller setting, with the input path/pin undecided. Cyberdeck reserves two full VIA ports for keyboard input and routes the console to keyboard/LCD. Controller uses serial and releases those ports to the application; firmware initially leaves them as inputs and does not scan or reconfigure them. LCD/I2C remains independently available. Auto/bank-preferred selection is a possible later extension, not an implemented metadata field. The profiles, switch circuit, keyboard interface, and electrical disconnect/isolation remain deferred. See [OPERATING-PROFILES.md](OPERATING-PROFILES.md).


## Host debugger boundary

`Machine.step()` executes one opcode and advances devices, with pending IRQ entry handled by `prepare_instruction()`. `Machine.run(n)` preserves the bounded instruction API. The debugger uses the same path, checking bank/address breakpoints after IRQ entry and before the next opcode. `MemoryBus.peek()` inspects without CPU-read side effects or time advancement. Stop requests are applied between complete execution chunks/instructions, without resetting the machine. See [DEBUGGER.md](DEBUGGER.md). These features do not alter firmware or the ROM layout.


## Shared firmware workspace and services

The implemented append-only service table now extends from `$E100` through `$E12A`. Kernel-owned RAM is ZP `$F0–$F3`, line buffer `$0280–$02EF`, serial scratch `$02F0–$02F1`, IRQ hook `$02F2–$02F3`, line state `$02F9–$02FB`, Port A shadow `$02FC`, LCD mode mailbox `$02FD`, and LCD buffer/state `$7F80–$7FFF`. Diagnostics retains `$02F4–$02F8`; Woz's `$0200–$027F` buffer and BASIC's user RAM `$0300–$7F7F` remain separate. BASIC staging assertions guard the workspace boundary. See [FIRMWARE-API.md](FIRMWARE-API.md). Serial services are non-reentrant and require controlled IRQ timing; polling returns quickly only when idle and is not background reception.

Serial RAM upload is implemented through `FW_LOAD`; see [Serial loader](SERIAL-LOADER.md). It accepts checksummed Intel HEX records of up to 16 data bytes, writes only `$0300–$7F7F`, and never launches automatically. Downloads and BASIC save/restore remain pending.

## Selected external serial/power interface

User selects an FT232RL USB-A cable described as six feet long with 5 V TTL UART and a six-way 0.1-inch female header exposing TX/RX/RTS#/CTS#/5 V/GND. Use it for board power from PC USB or a generic USB brick. Adopt the user-authorized **500 mA total USB design budget**, including converter consumption; actual cable rating is not independently verified. Pin order, board load, USB configuration/suspend behavior, cable voltage drop and input/inrush design remain electrical implementation work. See [BOM](BOM.md). No emulator change follows from this physical interface decision; the existing logical serial peer remains idle-high 8N1.

## Reserved system port and reusable mini bus

Accepted hardware reservation: VIA 1 PA0 TX, PA1 RX, PA2 I2C SDA, PA3 I2C SCL; PA4–PA7 form a reusable four-line GPIO mini bus, with SD SCK/MOSI/MISO//CS as the optional driver assignment. Include bus connector/SD module space in PCB design. SD software/model/filesystem are deferred. Unclaimed bus pins stay inputs with no default probing, and serial/I2C must preserve their latch/direction bits. Three other full VIA ports remain available before keyboard allocation. Serial/map migration is implemented; see [PINOUT.md](PINOUT.md).

## Reserved expansion connections

Provide three physical I/O headers: I/O 1 exposes VIA1 PB0–7 and CB1/CB2; I/O 2 VIA2 PA0–7 and CA1/CA2; I/O 3 VIA2 PB0–7 and CB1/CB2. Each includes +5 V/GND. This accounts for all 24 parallel bits and eight control lines outside VIA1's reserved Port A. No additional CPU address block is required. Selected connectors are three 1×12 and one 1×8 standard 2.54 mm male headers with numbered assignments in PINOUT.md; placement and external load limits remain PCB decisions; see [PINOUT.md](PINOUT.md). Keyboard allocation may later claim two ports only in the enabled profile.

VIA1 CA1/CA2 are exposed on the eight-contact mini bus; the three full-port headers each have twelve contacts. All ICs are DIP versions, with socket footprints in the KiCad draft. See [schematic guide](SCHEMATIC.md).

## LCD implementation

VIA1 PA2/PA3 drive open-drain-style I2C via direction changes. An optional modeled PCF8574 at default 7-bit `$27` consumes edges, acknowledges writes and drives HD44780 enable/data pins. `lcd_present` and `lcd_address` configure the Python device; firmware address is independent and must match. Actual backpack address/mapping is unconfirmed and must be verified at hardware bring-up. No firmware-PC trap or serial-text copying drives the LCD.

Mode 0 disables LCD, mode 1 mirrors/scrolls COUT on 20×4, mode 2 displays bank/system information and an application status line independently of serial. API slots `$E124/$E127/$E12A` select mode, clear and update dashboard status. `$02FD` is a cooperative firmware request mailbox; host commands do not asynchronously execute service code. A validated retained-RAM marker preserves mode through warm reset; firmware reinitializes the external LCD and updates bank identity. LCD contents are not physically reset by CPU reset; the model preserves device state and rebases remaining busy time across CPU cycle epochs.

Reserve ZP `$F2–$F3` and `$7F80–$7FFF` (128 bytes), even when off. BASIC's probe/explicit memory size and the serial loader stop at exclusive `$7F80`; diagnostic restoring scan covers `$0300–$7F7F`. LCD writes are synchronous; paced echo output follows completed LCD work. No background UART reception or automatic CPU-register telemetry is implied. See [LCD.md](LCD.md).

Current decode: [ADDRESS-DECODING.md](ADDRESS-DECODING.md). RAM `/CE` is A15 directly; ROM `/CE` is NAND(A15,A14). U4 selects A11–A13 with A15 high/A14 low enable. Y6/Y7 feed VIA1/VIA2; Y0–Y5 are spare. Optional extra RAM is not fitted or emulated. Existing LS21 reset-qualified write control remains.
