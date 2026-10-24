# Working on AMC-6502

AMC-6502 is a for-fun 6502 computer project. Development starts with a terminal-based emulator so firmware can be tested before hardware design.

## Read first

1. `README.md` — project overview and documentation index.
2. `docs/STATUS.md` — current state, verification, and next actions.
3. `docs/PLAN.md` — milestones and acceptance criteria.
4. `docs/DECISIONS.md` and `docs/MACHINE.md` — accepted decisions and machine contract.

These files provide context across agents and tools. Explicit user instructions take precedence. Distinguish accepted requirements, proposed defaults, and unresolved questions; do not turn a suggestion into a requirement without evidence.

## Working conventions

- Reuse existing components when practical. The selected CPU core is Py65; validate relevant classic NMOS 6502 behavior before depending on it.
- Start with terminal interfaces. Do not add a GUI or a custom CPU core without a reason agreed with the user.
- Install general-purpose tools through Ubuntu packages. Keep specialized tooling, including cc65, local to this project. Keep Python dependencies in `.venv/`.
- Pin external dependencies for reproducibility. Keep downloaded tools and generated artifacts out of Git.
- Firmware must exercise the modeled hardware interfaces. Avoid emulator shortcuts that conceal missing device behavior.
- Use deterministic emulated time and bounded runs for automated checks. Choose tests that verify observable machine behavior.
- Inspect the working tree before editing; preserve unrelated work. Do not claim a command or test passed unless it was run.

## Documentation is part of the work

Update documentation in the same change as implementation or design work:

- Update `README.md` when setup, usage, capabilities, or project direction changes.
- Update `docs/STATUS.md` with completed work, actual verification, limitations, and concrete next steps.
- Update `docs/PLAN.md` when milestones or scope change.
- Append significant accepted decisions to `docs/DECISIONS.md`, including rationale and consequences. Mark superseded decisions explicitly.
- Update `docs/MACHINE.md` when the emulated hardware contract changes.
- Add focused Markdown guides for substantial subsystems when needed and link them from the documentation index.

Keep status concise and current rather than maintaining a transcript. Record unresolved assumptions explicitly. At handoff, another agent should be able to identify what works, what was tested, and what to do next without chat history.

## Commands and current contract

`make setup` prepares pinned local cc65 and `.venv/`. `make test` assembles NMOS fixtures/ROM and runs integration tests; last implementation run passed 76. `make rom`, `make run`, `make test-api`, `make test-loader` and `make schematic-check` provide focused workflows. See docs/DEVELOPMENT.md.

- All ICs are DIP. Use `py65.devices.mpu6502.MPU` and ca65 `--cpu 6502`. Fixed 1 MHz clock uses the purchased active oscillator, assumed 5 V/half-size DIP8, exact model unknown. No divider or speed selector. Modern variants are separate experiments.
- Map: RAM `$0000–$7FFF`; VIA1 `$B000–$B7FF`, VIA2 `$B800–$BFFF` with register aliases every 16 bytes; unimplemented expansion `$8000–$AFFF`; selected 16 KB ROM `$C000–$FFFF`.
- Four ROM banks retain 8 KB personality/8 KB shared firmware; executable upper halves and vectors match except sole 32-byte metadata `$FFC0–$FFDF`. BASIC/idle/Woz/diagnostics occupy banks 0/1/2/3.
- Two physical toggles drive EEPROM A14/A15; hold reset while changing them. Reset retains positions/RAM. `$8020` is unpopulated expansion, not a selector. `$E106` stays fixed and returns unsupported; never restore software bank switching or a CPU-PC trap.
- VIA1 PA0 TX, PA1 RX, PA2 SDA, PA3 SCL; PA4–PA7 + CA1/CA2 form the mini bus. Full-port buses are VIA1 PB+CB, VIA2 PA+CA, VIA2 PB+CB. All include +5 V/GND. Selected male 2.54 mm headers are three 1×12 and one 1×8; docs/PINOUT.md defines numbered connections. Unclaimed pins remain inputs; preserve unrelated latches/directions.
- API 0.4.0 vectors append through `$E12A`; original `$E100/$E103/$E106` stay fixed. Use firmware/include/fw.inc. Kernel owns ZP `$F0–$F3`, line buffer `$0280–$02EF`, serial/IRQ `$02F0–$02F3`, line state `$02F9–$02FB`, Port A shadow `$02FC`, LCD request `$02FD` and LCD buffer/state `$7F80–$7FFF`. `$02F4–$02F8` is diagnostics-owned. BASIC/loader/user diagnostic scan end at `$7F7F`.
- Serial polling is idle-nonblocking, not background UART buffering. Loader at `$E121` validates complete records and preserves echo pacing. LCD MODE/CLEAR/STATUS at `$E124/$E127/$E12A` drive real VIA/I2C/PCF8574/HD44780 modeling, never copied serial text. Verify actual backpack address and mapping: `$27` is an unconfirmed default. See docs/LCD.md and docs/SERIAL-LOADER.md.
- Debugger is host-side. Use the normal instruction/IRQ/device-time path and side-effect-free peek; stop between instructions. Preserve bank-aware breakpoints and avoid raising inside CPU/device updates.
- Keyboard/profile and SD software remain deferred. Reserve removable 5 V SD module provision on the mini bus, but do not probe or claim it automatically.

## PCB and case handoff

Seven-sheet KiCad draft exists; no PCB layout/enclosure CAD/physical programming is complete. Keep native files canonical and document actual checks. Power/source/switch/USB off-state isolation is open PCB work; do not represent draft serial links as a completed power-safe circuit.

Mostly upright LCD leaning backward; bank/reset/power controls below it. Larger motherboard/bezel is allowed, particularly below LCD. **110 × 90 mm is the working placement-study envelope, not final size.** Retain LCD-relative four-hole mounting (reference 93 × 55 mm centers, actual module unverified), printed case/back, custom standoffs, brass inserts and four long retaining screws.

Socketed ICs face the LCD on motherboard top; all three full-port buses, mini bus and serial/power connection face rear-cover cutouts on motherboard bottom. Preserve electrical pin numbering and add rear-readable labels. Final tilt, spacer heights, screw/insert details, lower-board support, control footprints and cutouts remain open. Do not treat the former 98 × 60 mm motherboard outline as fixed. Next priority is a full-BOM placement trial and PCB/case clearance review; see docs/PCB-MECHANICAL.md and docs/PCB-FIT.md.

Current address decoder: LS138 takes A11/A12/A13, enabled for A15=1/A14=0; Y6/Y7 select the two 2 KB VIAs. RAM `/CE` is A15 directly and ROM `/CE` is NAND(A15,A14). LS138 pin 8 is GND, pin 7 Y7. LS21 remains for reset-qualified writes; no second decoder/extra RAM is fitted. Firmware hardware.inc and Python memory_map.py define the VIA bases. Do not resurrect the earlier 47 KB/512-byte-VIA proposal. J2 exposes six spare selects and rails, not a full CPU expansion bus. See docs/ADDRESS-DECODING.md.
