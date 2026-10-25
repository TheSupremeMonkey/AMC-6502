# AMC-6502 (AstroMonkey Micro Computer)

A for-fun classic 6502 computer developed with a terminal emulator and real assembled firmware before building hardware. The target is a compact retro desktop terminal that can also serve as an embedded controller.

## Current state

The emulator and 64 KB ROM run Microsoft BASIC (bank 0), an idle placeholder (bank 1), Woz Monitor (bank 2), and RAM/VIA diagnostics (bank 3). Shared firmware ABI 0.4.0 provides serial, console helpers, Intel HEX RAM upload, LCD console mirroring and an independent status dashboard. The host debugger supports run/stop/step, bank-aware breakpoints and safe memory inspection. The last implementation verification passed **76 tests**.

A seven-sheet KiCad 9 schematic draft exists, with zero ERC violations at the last check. **PCB placement/routing, enclosure CAD, physical flashing and hardware bring-up remain to do.** Current state and next actions are in [STATUS](docs/STATUS.md) and [PLAN](docs/PLAN.md).

## Desktop case direction

Mostly upright LCD, leaning backward, in a compact 1970s-terminal-style 3D-printed enclosure. Bank toggles, reset and power controls sit below the LCD. The motherboard may extend below the display and use a wider bezel; **110 × 90 mm is the working placement-study envelope, not a frozen board size**. The original 98 × 60 mm LCD-sized motherboard proved crowded in a footprint-area assessment.

Retain the LCD-relative four-hole mounting pattern, custom standoffs, brass inserts and four long screws retaining the boards and removable case back. Socketed DIP ICs face the LCD on motherboard top; three full-port buses, mini bus and serial/power connection face rear-cover cutouts from motherboard bottom. Exact LCD dimensions, viewing angle, spacer heights, controls and cutouts await placement/mechanical review. See [mechanical plan](docs/PCB-MECHANICAL.md).

## Development and use

```sh
make setup
make test
make run
```

Use `:help`, `:run`, Ctrl-C to pause, `:bank 1`–`:bank 4` for manual toggle/reset simulation, and `:reset` to retain the current bank. `:lcd mirror`, `:lcd dashboard`, `:lcd off` request display modes; `:lcd` inspects four rows. `make rom` rebuilds the image and `make schematic-check` exports/checks the KiCad draft. General tools use Ubuntu packages, cc65 stays project-local, and pinned Python dependencies live in `.venv/`. See [development setup](docs/DEVELOPMENT.md).

## Hardware and implemented map

All ICs are DIP. Baseline is the original MOS NMOS 6502 (date code 0284) and two classic MOS 6522 VIAs at a fixed **1 MHz**, HM62256ALP-10 100 ns RAM and W27C512-45Z 64 KB ROM. The purchased active oscillator is assumed 5 V in the supplied half-size DIP8/four-lead package; no divider or selectable clock. Modern CPU substitution remains a separate experiment.

| CPU range | Allocation |
| --- | --- |
| `$0000–$7FFF` | 32 KB physical RAM; firmware reserves workspace including top 128 bytes |
| `$8000–$AFFF` | Six unpopulated 2 KB expansion slots; reads `$FF`, writes ignored |
| `$B000–$B7FF` | VIA1, 16 registers repeated throughout the 2 KB block |
| `$B800–$BFFF` | VIA2, 16 registers repeated throughout the 2 KB block |
| `$C000–$DFFF` | Selected bank's 8 KB personality |
| `$E000–$FFFF` | 8 KB shared firmware; only bank metadata `$FFC0–$FFDF` differs |

A15 directly enables low RAM; NAND(A15,A14) enables ROM. The 74LS138 decodes the intervening 16 KB into eight 2 KB slots, with VIAs on Y6/Y7. Extra RAM remains optional and unpopulated. Two manual bank toggles supply EEPROM A14/A15. Hold RESET while changing them, then release; reset alone retains positions and RAM. `$8020` is an unpopulated expansion address, not a software selector. The retired `$E106` service returns carry set. All four ROM banks together fill the 64 KB device.

VIA1 PA0 is serial TX, PA1 RX, PA2 I2C SDA and PA3 SCL. PA4–PA7 plus CA1/CA2 form the 1×8 mini bus. Three 1×12 full-port buses expose VIA1 PB+CB, VIA2 PA+CA and VIA2 PB+CB. Every header includes switched +5 V/GND and uses standard 2.54 mm male through-hole pins for DuPont leads; exact numbered assignments are in [PINOUT](docs/PINOUT.md). Keyboard ownership and SD software remain deferred.

LCD is 20×4 through a PCF8574 backpack; **verify the actual 7-bit address and wiring before hardware bring-up**. `$27` is an unconfirmed development default. LCD state/buffer reserves `$7F80–$7FFF`, so BASIC and serial uploads end at `$7F7F`. Mirror mode scrolls console output; dashboard mode keeps bank/system information and an application-updated status line independent of serial. See [LCD guide](docs/LCD.md).

Selected power/serial interface is a six-foot FT232RL 5 V TTL USB cable. Its actual current rating and pin order remain unverified. Power/source options and USB off-state isolation are PCB work; the draft is not a validated power circuit. User owns an XGecu T48 programmer; full erase/program/readback verification remains pending. See [BOM](docs/BOM.md) and [power budget](docs/POWER-BUDGET.md).

## Documentation index

| Document | Purpose |
| --- | --- |
| [Pro Micro bring-up](chip-tester/README.md) | Isolated PlatformIO environment; WSL upload/readback, USB serial and onboard blink verified |
| [AGENTS.md](AGENTS.md) | Instructions and reading order for agents and tools |
| [LCD console and dashboard](docs/LCD.md) | Modes, firmware API, address verification and RAM reservations |
| [Serial RAM loader](docs/SERIAL-LOADER.md) | Intel HEX upload, sender commands, protocol, and protections |
| [Shared firmware API](docs/FIRMWARE-API.md) | Stable vectors, calling conventions, line editor, polling, and RAM ownership |
| [Terminal debugger](docs/DEBUGGER.md) | Run/stop, Ctrl-C pause, steps, breakpoints, registers, and RAM editing |
| [Operating profiles](docs/OPERATING-PROFILES.md) | Planned Cyberdeck/Controller selection and port ownership |
| [Optional keyboard planning](docs/KEYBOARD.md) | Available keyboards, Atmos preference, and optional PIO ownership |
| [Shared firmware concept](docs/FIRMWARE-CONCEPT.md) | Proposed complete top-8-KB services, boundaries, and implementation order |
| [Changing ROM banks](docs/ROM-SWITCHING.md) | Manual toggles, reset and emulator host controls |
| [Bank 3 diagnostics](docs/DIAGNOSTICS.md) | Running checks, side effects, and failure coverage |
| [Classic VIA model](docs/VIA.md) | Register/timer behavior, IRQ wiring, tests, and fidelity limits |
| [Banked firmware](docs/FIRMWARE.md) | BASIC/Woz ROM build, terminal use, source pins, and limitations |
| [Development setup](docs/DEVELOPMENT.md) | Prerequisites, local tools, build and test commands |
| [Development plan](docs/PLAN.md) | Milestones and acceptance criteria |
| [Current status](docs/STATUS.md) | Implemented work, verification, and next actions |
| [Design decisions](docs/DECISIONS.md) | Accepted choices and rationale |
| [SD storage proposal](docs/SD-CARD.md) | Reserved PA4–PA7 mini bus, optional 5 V SD module provision, deferred software |
| [Planned VIA/LCD pinout](docs/PINOUT.md) | Physical VIA pins, LCD wiring and single-row expansion headers |
| [Pre-placement schematic audit](docs/SCHEMATIC-AUDIT.md) | Core coverage, unfinished interface circuitry and physical parts to close |
| [Address decoding](docs/ADDRESS-DECODING.md) | Corrected LS138/NAND wiring and eight 2 KB slots |
| [Extra RAM proposal](docs/RAM-EXPANSION.md) | Possible second SRAM and smaller I/O windows; not implemented |
| [PCB fit assessment](docs/PCB-FIT.md) | Measured DIP/socket area and placement feasibility |
| [KiCad schematic](docs/SCHEMATIC.md) | Native project, exports, verification and open circuitry |
| [PCB outline and LCD mounting](docs/PCB-MECHANICAL.md) | Upright desktop case, larger motherboard, LCD mounting and stack clearances |
| [Reset circuit](docs/RESET.md) | Retro RC/Schmitt reset, manual button, parts, and board-level checks |
| [Power budget](docs/POWER-BUDGET.md) | Estimated current draw, display allowances, and power-path sizing |
| [Draft hardware BOM](docs/BOM.md) | Known parts, candidate quantities, compatibility checks, and decisions before buying |
| [Hardware decoding proposal](docs/HARDWARE-PROPOSAL.md) | Historical proposal and superseded alternatives; use MACHINE for current contract |
| [Machine contract](docs/MACHINE.md) | Working memory map, reset semantics, and open hardware questions |
