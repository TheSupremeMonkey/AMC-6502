# Design decisions

Record significant decisions with their status, rationale, and consequences. Proposals are not accepted requirements. Entries retain historical context; use STATUS.md/PLAN.md for the current handoff.

Current supersession map: D024/D025 replace selectable/bare-crystal clock alternatives; D028/D036 retire software/cycling bank control; D034 moves VIA1 CA1/CA2 to the mini bus; D038 selects single-row headers; D039 replaces LCD deferral and reserves upper RAM; D042 relaxes the LCD-sized motherboard outline. D043 explicitly places serial and mini bus at the rear. D044 replaces the former 4 KB decode with eight 2 KB slots, keeping extra RAM deferred.

## D001 — Emulator before hardware

Accepted: 2026-10-23, user direction.

Develop the emulator and test software before designing the physical board. The README hardware concept is a starting point, not a finalized schematic. Keep assumptions explicit so software testing can inform hardware decisions.

## D002 — Reuse components; terminal first

Accepted: 2026-10-23, user direction.

Reuse as much as practical and start with a terminal interface. Py65 is the planned CPU core and cc65's ca65/ld65 the planned firmware toolchain. Their precise revisions and compatibility remain to be verified. A custom CPU implementation and GUI are outside initial scope.

## D003 — Project-local specialized tools

Accepted: 2026-10-23, user direction.

Install general-purpose tools through Ubuntu packages. Keep specialized tools such as the 6502 assembler/linker local to the project. Use `.tools/` for these tools and `.venv/` for Python dependencies; pin versions and ignore generated/downloaded contents.

## D004 — Bank switching resets the machine

Status note: Bank cycling is superseded by D028/D036; separate manual toggles and reset are current.

Accepted: 2026-10-23, user direction.

The bank button selects the next bank and performs a full reset. There are no suspended sessions or live software bank swaps. Bank selection must survive the reset, so the earlier proposal to rely solely on VIA output state needs revision before hardware design.

Mirrored kernel code is no longer required for safe live switching. Whether common firmware is duplicated in each bank remains a layout decision. RAM retention and exact peripheral reset behavior remain proposed details in the machine contract.

## D005 — Durable Markdown context

Accepted: 2026-10-23, user direction.

Keep the README current and maintain additional Markdown planning, status, and technical documentation. Provide tool-neutral `AGENTS.md` guidance so different agents and tools can continue without relying on chat history.


## D006 — Classic chips throughout

Amended by D010 to permit experimental modern CPU variants.

Accepted: 2026-10-23, explicit user correction.

All firmware and emulated hardware target classic chips. The CPU is the original NMOS 6502, not a CMOS successor; the VIAs target classic 6522 parts. This supersedes the original README's modern WDC CPU/VIA assumptions. Use Py65's `mpu6502` core and ca65's `6502` CPU mode. Do not depend on CMOS instructions, modern peripheral enhancements, or unverified high clock rates. Exact manufacturer variants and speed grades remain to be selected.

## D007 — Initial toolchain pins

Implemented: 2026-10-23.

Use cc65 V2.19 at commit `555282497c3ecf8b313d87d5973093af19c35bd5` and Py65 1.2.0 with a pinned wheel hash. Python standard-library unittest supplies the initial test runner. The smoke ROM tests the toolchain using upstream flat memory; it does not establish AMC device fidelity.


## D008 — Jumper-selectable 1–16 MHz clock

Superseded by D009. Originally accepted: 2026-10-23, user direction.

Target a classic 1 MHz-rated chip and provide jumper-selectable clocks at every integer MHz from 1 through 16 MHz. Settings above the rating are experimental overclocking. This supersedes the original power-of-two clock options and binary-divider circuit proposal; the new clock-generation circuit remains undecided. Emulated nominal clock selection does not establish physical chip or peripheral timing compatibility.


## D009 — Binary clock settings; 1/2 MHz intended

Superseded by D024: the current hardware clock is fixed at 1 MHz.

Accepted: 2026-10-23, user direction. Supersedes D008.

Provide jumper-selectable **1, 2, 4, 8, and 16 MHz** settings from a 16 MHz oscillator with binary divide-by-two stages and a 16 MHz bypass. Intended operating speeds are 1 and 2 MHz; all higher settings are entirely experimental. The initial 1 MHz-rated CPU target does not guarantee 2 MHz operation; confirm actual CPU and peripheral ratings. Counter part/family, timing, and jumper wiring remain open. This restores the binary-divider approach without finalizing the original 74HC393 part choice.


## D010 — Classic baseline with experimental modern CPU variants

Accepted: 2026-10-23, user direction. Amends D006; retains D009 clock settings.

Design for classic 6502 compatibility by default. Leave modern 6502-family CPU variants as an experimental option that may support the higher clock settings. Preserve classic-compatible baseline firmware and explicitly configure and test any variant-specific CPU core, instructions, or behavior. No alternate configuration is implemented yet. Modern CPU availability does not guarantee pin compatibility or high-speed operation of RAM, VIAs, decoding, or the clock circuit; select exact parts and validate the complete system.


## D011 — Initial single-bank emulator defaults

Implemented: 2026-10-23 as reversible defaults for the first diagnostic.

Load exactly 8 KB ROM, zero-initialize RAM for deterministic runs, ignore ROM writes, and temporarily return `$FF` for unimplemented I/O/reserved reads while ignoring their writes. Reset retains RAM, resets the cycle counter, and sets IRQ-disable explicitly over Py65's default. These choices enable bounded firmware tests; they do not define physical open-bus or power-on behavior. Four-bank reset behavior and device models are subsequent work.


## D012 — Four 16 KB ROM banks with mirrored 8 KB system firmware

Accepted: 2026-10-23, user clarification.

Each bank has a full lower 8 KB for BASIC/monitor/personality code and an upper 8 KB for all shared system functions, identical across all four banks. Four 16 KB banks fill the 64 KB EEPROM. The working CPU map is `$C000–$DFFF` for payload and `$E000–$FFFF` for shared firmware, retaining RAM and VIA addresses. This supersedes the original 8 KB window and 6 KB/2 KB split. At decision time, code still implemented the older single 8 KB fixture; the banked implementation is recorded in D013. Exact entry points, reset dispatch, and bank metadata placement remain open.


## D013 — First BASIC/Woz banked image

Accepted scope: 2026-10-23, user request; implemented and tested.

Build a 64 KB image with Microsoft BASIC in bank 0, Woz Monitor in bank 2, and idle placeholders in banks 1/3. This supersedes earlier proposed monitor/cyberdeck bank assignments. Use pinned upstream sources and stage ca65-compatible adaptations under `build/`, keeping upstream checkouts clean. The built BASIC is the msbasic OSI configuration; the official Microsoft V1.1 source is downloaded separately for reference, not assembled verbatim.

Shared upper halves are identical, including reset/vectors and provisional console entry points at `$E100`/`$E103`. Reset initializes hardware and enters payload `$C000`. Real firmware bit-bangs VIA PA0/PA1; the emulator supplies a cycle-scheduled serial peer and a minimal port-A model. Fixed delays currently support only the 1 MHz baseline. No emulator-PC console traps are used. See `FIRMWARE.md` for provenance, build details, tests, and limitations.


## D014 — Classic VIA timers and shared CPU IRQ

Implemented: 2026-10-23, user-authorized next development step.

Model both classic VIAs at their planned addresses, combining enabled pending sources onto the CPU's level IRQ input. Add ports/input latching, control-input flags, T1 one-shot/free-running and PB7, T2 interval/pulse counting, IFR/IER, and reset. Verify with a separate assembled firmware fixture and preserve BASIC/Woz serial regression coverage. Production common firmware still masks interrupts; no background IRQ service is enabled there yet.

Use explicit integer PHI2 timing with load/reload delay and document instruction-boundary access/IRQ limitations. Timer reset contents are deterministic emulator defaults. Reject active shift modes and timed CA2/CB2 handshake/pulse output modes until implemented. Exact physical IRQ wiring, timing races, and manufacturer-specific quirks remain unvalidated; see `VIA.md`.


## D015 — Bank 3 diagnostics and shared IRQ dispatch

Accepted: 2026-10-23, user request; implemented. Supersedes the bank 3 placeholder in D013.

Bank 3 automatically runs restoring `$55`/`$AA` RAM checks over `$0300–$7FFF` and bounded one-shot timer/IRQ checks for T1/T2 on both VIAs. Print individual PASS/FAIL results and a summary through shared console drivers; accept `R` to rerun. Do not change expansion port output configuration. Document workspace clobbering and peripheral side effects.

Keep the common upper 8 KB identical. Add a RAM IRQ hook at `$02F2–$02F3`, initialized by the shared reset handler to a default RTI handler; diagnostics installs its own handler with interrupts masked. NMI remains a separate default RTI path. Other personalities still start with interrupts masked, and every bank reset restores the default hook. Validate normal execution, RAM restoration, rerun, failure paths, and existing personalities.


## D016 — Shared retro boot banner

Accepted: 2026-10-23, user request; implemented.

Print a compact ASCII rocket and AstroMonkey identity from shared firmware on every reset before entering the bank payload. Keep identical upper halves and use the real console driver. Separate banner code/data from serial timing loops. Report configured capabilities without inventing passed POST checks. Increase the terminal instruction slice to 1,000,000 so the banner and bank 3 diagnostics can complete before accepting rerun input.


## D017 — Bank-specific description in the shared ROM region

Accepted: 2026-10-23, user request. Amends D012/D013/D015/D016's strict upper-half mirroring.

Reserve `$FFC0–$FFDF` in every bank for a 32-byte zero-padded, null-terminated ASCII description. The common banner reads that bank's record directly and prints its number/personality. Every other upper-half byte, including code, console ABI, and CPU vectors, remains identical. The linker reserves the field, the builder validates/fills it, and tests exempt only that exact field from mirroring comparisons. This supersedes the original proposed `$FFE0–$FFEF` metadata location.


## D018 — Software bank vector and numeric diagnostics menu

Status note: Superseded by D028/D036: software switching is retired.

Accepted: 2026-10-23, user request; implemented as a provisional hardware contract.

Expose shared vector `$E106`: A=0–3 requests a bank and full reset, without returning; invalid values return carry set. Use a modeled persistent selector/reset register at `$8020`, reading current bank and accepting writes 0–3. Apply reset after the write instruction, retaining RAM and bank state. Physical decode/latch/button/reset circuitry remains to be designed; this is not an intrinsic VIA or CPU feature.

The diagnostics menu maps user choices 1–4 to physical banks 0–3. `R` reruns without reset. Avoid intercepting numeric input in BASIC/Woz. Add host `:bank 1` through `:bank 4` for direct selection anywhere; track reset generation so firmware-triggered reset output is visible.


## D019 — Cyberdeck/Controller profile planning

Accepted: 2026-10-23, user agreement; implementation explicitly deferred.

Plan one reconfigurable board: Cyberdeck uses keyboard/LCD and reserves two full VIA keyboard ports; Controller uses serial and releases those ports to application ownership, with the LCD independently available. Sample a mechanical jumper/DIP profile setting at reset. The physical input path, pin assignments, keyboard interface, and isolation arrangement remain undecided. Firmware must not scan or reconfigure released keyboard ports.

A common ROM image should be able to support both uses; specialized controller images remain an option. Banks should describe supported profiles when this feature is implemented. Auto selection using bank preferences is a possible later extension; neither a three-position switch nor a metadata encoding is finalized. See `OPERATING-PROFILES.md`. No profile/keyboard implementation is included in this documentation change.


## D020 — Host terminal debugger

Accepted: 2026-10-23, user-authorized next software step; implemented.

Add continuous execution, boundary-safe stop/Ctrl-C, CPU registers, non-destructive memory inspection, validated RAM editing, single/multiple instruction stepping, and bank-aware address breakpoints. Keep these host-side: no ROM opcodes patched and no firmware size/interface changes. Preserve bounded startup/input slices and existing bank commands. Breakpoint checks occur before opcode execution, after any pending IRQ entry; resume skips the hit once.

Use a single-owner event loop with short execution chunks and a SIGINT stop flag rather than asynchronous exceptions inside machine updates. Use device peek paths so inspection cannot acknowledge flags or consume serial input. Retain the machine's cycle/IRQ/reset behavior. Keyboard/profiles and higher-clock support remain deferred. See `DEBUGGER.md`.


## D021 — Shared firmware service API and RAM ownership

Accepted: 2026-10-23, user-authorized software step; implemented.

Retain the original three vectors and append PUTS, HEX8/16, READLINE, CIN_POLL, VERSION, BANK_GET, and CRLF through `$E11E`. Define the contract in `FIRMWARE-API.md` and publish constants in `firmware/include/fw.inc`. Reserve ZP `$F0–$F1`, line buffer `$0280–$02EF`, serial/IRQ scratch `$02F0–$02F3`, and line state `$02F9–$02FB`; retain diagnostics' `$02F4–$02F8`. Guard BASIC's workspace at build time rather than shrinking its existing user-RAM area.

Use bounded string scans and an edited, NUL-terminated line buffer with explicit limits/status. Keep serial services non-reentrant and honest about polling: idle calls return immediately, but receiving a byte takes a character time and requires frequent polling, not arbitrary background computation. Reuse the common string service in startup/diagnostics. Verify through assembled code and VIA pin-level serial. LCD, keyboard/profiles, and higher-clock support remain deferred.


## D022 — Checksummed serial RAM upload

Implemented: 2026-10-23, user-authorized next software step.

Append FW_LOAD at `$E121` and bump API to 0.2.0, preserving all prior vectors. Reuse Intel HEX with 0–16-byte data records and EOF, character-echo pacing and per-record acknowledgements for the unbuffered bit-bang console. Validate whole records before writing only `$0300–$7FFF`; reject other types/ranges and never automatically execute. Partial uploads retain earlier accepted records. Diagnostics L invokes the common service; the stdlib Python sender supports a fresh emulator and POSIX serial devices. Keep workspace inside existing line buffer/PUTS pointer. Verify actual assembled firmware over modeled pins. Physical serial validation, download, and BASIC storage remain future work.


## D023 — 4 KB chip selects with existing 16 KB ROM banks

Status note: slot granularity and ROM-select implementation superseded by D044; retain the four 16 KB bank layout.

Accepted: 2026-10-23, explicit user clarification of the hardware proposal.

Use A15 for the RAM/upper-space split and an upper-space 138 decoder driven by A12–A14. Assign Y0 to VIA 1, Y1 to VIA 2, Y2/Y3 to expansion, and Y4–Y7 to ROM. Retain `$C000–$DFFF` personality and `$E000–$FFFF` common kernel, four 16 KB banks, and the 64 KB EEPROM image. This supersedes the immediately preceding proposal's 8 KB banks, 2 KB kernel, and 32 KB EEPROM footprint; existing ROM layout and ABI remain valid. EEPROM bank signals must drive A14/A15, not A13/A14.

Target VIA blocks are `$8000–$8FFF` and `$9000–$9FFF` with register aliases. Existing `$8020` selector conflicts with that decode. Bank/reset wiring and its replacement software interface remain unresolved; do not silently treat VIA-controlled bank selection as preserving a full VIA reset. Emulator/I/O migration is pending those answers; see `HARDWARE-PROPOSAL.md`.


## D024 — Fixed 1 MHz clock

Accepted: 2026-10-23, explicit user instruction: "Let's just lock in at 1mhz".

Lock the current board to 1 MHz with the owned MOS 6502 and classic 6522 VIAs. Supersedes D009's selectable 1/2/4/8/16 MHz clock and any remaining higher-clock requirement from D008/D010. No speed-selection jumper, binary divider, or higher-speed firmware/emulator configuration is required. A direct 1 MHz oscillator module is the simplest BOM candidate; exact part and clock distribution still need electrical/timing verification. Existing firmware/serial-peer timing already matches 1 MHz, so no code changes are needed. Modern CPU variants remain a separate experimental possibility, without a current selectable-clock requirement.


## D025 — Purchased active 1 MHz oscillator, assumed 5 V

Accepted: 2026-10-23, explicit user purchase and design instruction.

Use the purchased 1 MHz active oscillator from the AliExpress listing, assume its 5 V version, and adopt the supplied ECS-2100 half-size DIP-8/four-lead mechanical/pinout reference. Exact oscillator model is not listed; do not assert ECS manufacture. This settles D024's clock-source choice and supersedes later bare-crystal/divider candidates. Remove separate crystal, oscillator amplifier, feedback/load network, divider, and speed jumper from the board BOM. Keep local bypassing and design reset/clock routing to the reference requirements. Existing firmware/emulated serial already uses 1 MHz; no code change is needed. Physical delivery and electrical verification are not claimed.


## D026 — FT232RL USB serial/power cable and assumed 500 mA budget

Accepted: 2026-10-23, explicit user interface choice and current-budget assumption.

Use the described six-foot FT232RL USB-A to 5 V TTL cable, six-way 0.1-inch female header, for console and 5 V board power from PC USB or a generic USB brick. Interpret the contextual "500mv" reply to the current question as **500 mA** and adopt it as the total USB design budget, including interface consumption. Do not treat this as a verified cable current rating or unconditional USB entitlement. The exact cable model/pin order is unspecified; its stated 5 V UART levels are accepted for planning. Engineer board load, cable drop, input/inrush/reset and USB power states; retain any future auxiliary-source isolation as separate work. No default second supply or regulator is required by this decision. See `BOM.md` for relevant manufacturer references and outstanding validation. Emulator serial behavior is unchanged.


## D027 — Power options at PCB design

Accepted: 2026-10-23, explicit user direction after reviewing the current estimate.

Design power-input options during actual PCB design. Keep the FT232RL interface and preliminary power budget as context; defer connector, auxiliary source, source-selection/isolation and protection choices. This is not approval of the unknown cable rating or parallel supply wiring, and does not require an immediate new cable/supply purchase. Use measured loads and the current budget when selecting those PCB circuits.


## D028 — Manual bank toggles and separate hardware reset

Accepted: 2026-10-23, explicit user confirmation: "Yes toggle bank and a hardware reset."

Use two toggle switches driving EEPROM A14/A15 and a separate button resetting CPU and both VIAs. Hold reset during selection and allow contacts to settle before release. Power-on follows toggle positions; reset does not change them. No software writable bank selector, bank counter, bank-advance button or VIA bank outputs are required. PA2/PA3 and CA1 become available. The bank display can consume the same switch signals.

Supersedes D004/D018 software/cycle/select-and-reset requirements and the electronic-selector alternatives for the physical board. Preserve D012/D017 ROM layout and metadata exception. Existing emulator register/vector/menu behavior remains legacy code pending coordinated 4 KB I/O migration; retire it rather than retain an emulator shortcut absent in hardware. Host bank controls should represent external switches/reset, and current-bank queries need ROM metadata or explicitly modeled wired inputs. This decision does not select exact switches/reset components or claim implementation/testing has changed.


## D029 — Board power switch with USB review at PCB design

Accepted: 2026-10-23, explicit user instruction.

Add one board power switch to the BOM, separate from bank toggles and hardware reset. Track an open PCB action to account for USB and switch behavior: PC/brick operation, power ON/OFF paths, powered FT232 signal back-feeding, any auxiliary-source isolation, current/voltage/inrush and power-up reset. Keep ground continuous; exact switch/circuit/footprint is deferred to PCB design under D027. This accepts the control, not a claim that switching cable VCC alone provides a validated OFF state.


## D030 — Retro RC/logic reset instead of supervisor

Accepted: 2026-10-23, user preference for an old-school simple retro circuit.

Replace the DS1813 recommendation with an RC delay feeding Schmitt-trigger logic and a manual discharge button. Two 74LS14 gates are the recommended active-low implementation; resistor/capacitor values remain proposed until timing and electrical verification. Add reset timing capacitance to the BOM; no dedicated supervisor purchase. Preserve hardware CPU/VIA reset independent of manual bank toggles. Explicitly check slow USB supply ramps, rapid off/on, oscillator startup, reset fanout and RAM write control; this circuit is not a precision brownout monitor. See `RESET.md`.


## D031 — Use owned 74HC14 for buffered RC reset

Accepted: 2026-10-23, user confirms owning a 74HC14 and selects the cleaner buffered option.

Use two gates of the owned HC14 to produce active-low reset for CPU and both VIAs. Supersedes D030's LS14 recommendation and the unbuffered four-part alternative. Prototype circuit uses 10 kΩ, 10 µF, 1 kΩ sense/discharge limiter, 1N4148 and button, plus normal IC bypass. Pin-numbered drawing and connections are in `RESET.md`; values/actual supply timing still need bench verification. HC14 input is its own RC network, so this choice does not change the general NMOS-to-HC level-compatibility checks elsewhere. Keep clock running, bank switches independent, and USB/switch PCB action open.


## D032 — Reserve four-line mini bus, SD software later

Accepted: 2026-10-23, explicit user instruction to reserve the pins, include them in the PCB and defer SD software.

VIA 1 PA0/PA1 are serial TX/RX; move I2C SDA/SCL to PA2/PA3. Reserve PA4–PA7 as a generic four-line mini bus, with optional SD SPI use SCK/MOSI/MISO//CS. Include routing/connector and module space for a removable 5 V Arduino-style SD module; exact module/fitting/footprint remain PCB decisions. Software/card emulation/filesystem testing and implementation are deferred. Default firmware does not claim or probe the bus; retain input state until claimed and preserve its latch/direction state in other drivers. Electrical module isolation/loading must permit actual reuse. This supersedes the earlier PA4/PA5 I2C planning allocation; current ROM/emulator migration remains pending. Keep SD peak-current accounting in the PCB power work.


## D033 — Three full-port I/O expansion connections

Status note: Control-pair grouping revised by D034; preserve the three full-port requirement.

Accepted: 2026-10-23, explicit user request for three I/O expansions with remaining VIA pins, power and ground.

Reserve I/O 1 for VIA1 Port B plus CB1/CB2 and spare CA1/CA2, I/O 2 for VIA2 Port A plus CA1/CA2, I/O 3 for VIA2 Port B plus CB1/CB2. Each includes +5 V and GND; all remaining 24 GPIO bits and eight control lines are exposed, retaining VIA1 Port A's serial/I2C/mini-bus reservation. Header geometry/pin order/current limits remain PCB choices. Replaces the original per-signal three-pin-cluster expansion proposal. No extra bus-controller/decode IC is mandated by connector routing. Preserve keyboard profile ownership and electrical isolation; firmware does not claim unassigned pins. See `PINOUT.md`.


## D034 — Mini bus control pair and identical full-port headers

Accepted: user confirms the refined grouping. Supersedes D033's placement of VIA1 CA1/CA2 on I/O 1. Put that pair on the mini bus; mini has eight contacts and all three full-port headers have twelve. All eight control signals remain exposed. Mechanical header defaults in the schematic remain subject to PCB review.

## D035 — DIP ICs and selected owned SRAM

Accepted: explicit user instructions. All ICs are DIP versions. Select the owned HM62256ALP-10 (100 ns, wide DIP28) for the draft; use socket footprints. Exact oscillator manufacturer remains unknown, with the previously accepted 5 V/package assumption. Native KiCad draft uses 74LS138/74LS21/74LS00 decode/write logic and owned 74HC14 reset; connectivity checks do not replace bench/timing qualification.


## D036 — Implement schematic contract; defer LCD

Status note: LCD deferral superseded by D039 and 4 KB VIA decode by D044; manual banking remains implemented.

Accepted: user requests emulator migration to the new schematic and explicitly skips LCD. Implement 4 KB mirrored VIA blocks at `$8000`/`$9000`, unassigned `$A000–$BFFF`, four manual 16 KB ROM banks and separate reset, PA0 TX/PA1 RX. Retire `$8020` selector and numeric software switching; preserve `$E106` slot as an unsupported return. Query bank via ROM metadata. Firmware ABI becomes 0.3.0; Port A latch shadow at `$02FC` preserves other reserved bits. Host controls represent external switches/reset, not a software-accessible device. LCD/I2C, keyboard and SD remain deferred. The 1 MHz target is settled; routine wiring review is not an outstanding component-speed decision.


## D037 — Standard expansion pin headers

Status note: Double-row defaults superseded by D038; standard 2.54 mm header requirement remains.

Accepted: user selects standard pin headers for three 12-contact buses and the mini bus. Use standard 2.54 mm through-hole male headers, three 12-pin and one 8-pin. Existing KiCad 2×6 and 2×4 vertical footprints remain the layout defaults, rather than imposing a new row arrangement. Signal assignments and emulator behavior are unchanged; placement/orientation remains PCB work.


## D038 — Single-row bus headers for DuPont cables

Accepted: explicit user correction. Three 1×12 and one 1×8 standard 2.54 mm through-hole male pin headers, for standard DuPont leads. Supersedes D037's retained double-row layout defaults. KiCad J6–J8 use single-row 12-pin symbols/footprints; J9 uses single-row 8-pin. Existing pin-to-signal assignments are retained. No emulator/firmware behavior changes.


## D039 — LCD console mirror and independent application dashboard

Accepted: user requests both LCD modes and explicitly requires an action to verify the actual I2C address. Shared NMOS firmware implements off, scrolling 20×4 COUT mirror, and independent dashboard with bank/system information plus application-updated status. Serial remains available. Both modes drive VIA1 PA2/PA3 through real I2C/PCF8574/HD44780 modeling; no serial-copy or CPU-PC shortcuts. LCD_ADDRESS `$27` and common backpack mapping are development assumptions, not confirmed hardware. Verify actual address and mapping at physical bring-up.

Implementation allocates 128 bytes `$7F80–$7FFF`, ZP `$F2–$F3` and mode mailbox `$02FD`; BASIC/loader/diagnostics exclude reserved RAM. Services append at `$E124/$E127/$E12A`, ABI 0.4.0. Cold emulator defaults off; validated retained RAM preserves a requested mode through warm reset. This supersedes D036's LCD deferral only; keyboard/SD remain deferred. Writes are synchronous; serial echo follows LCD work to preserve uploader pacing. No background serial reception or automatic CPU-register telemetry is promised.


## D040 — Match PCB outline and four mounting holes to LCD

Status note: Strict matching-outline constraint relaxed by D042; LCD-relative mounting-hole alignment remains.

Accepted: user requests an LCD-sized motherboard with matching four holes. Plan a stacked assembly; spacer height and component orientation remain open. Online manufacturer reference is nominal 98 × 60 mm, four 2.5 mm LCD holes on 93 × 55 mm centers, inset 2.5 mm. These numbers are provisional until the actual module is identified/measured; do not equate all LCD2004 modules or claim the DIP layout already fits. See PCB-MECHANICAL.md for sources, derived coordinates and clearance actions.


## D041 — Printed LCD enclosure and four-screw board stack

Accepted: user specifies a 3D-printed case, custom standoffs, brass inserts and four long screws retaining the board stack and case back. Motherboard ICs/sockets face the LCD; peripheral headers mount on the opposite bottom side with access cutouts in the rear cover. Preserve selected 1×12/1×8 headers and electrical pin numbering. This settles D040's component-side orientation; exact spacer heights, screw/insert dimensions and locations remain open. Rear screw entry into front-shell inserts is only a possible implementation. No PCB placement or enclosure CAD is claimed. See PCB-MECHANICAL.md.


## D042 — Upright desktop terminal with lower controls; allow larger board

User direction: explore a larger bezel/motherboard, with the board extending below the LCD and a supporting base. User explicitly chooses a mostly upright display leaning backward, and locates toggles/buttons below the LCD. This relaxes D040's strict matching-outline target as an allowed design option while preserving its shared four-hole mounting pattern and D041's stack orientation/four-screw enclosure. Exact board dimensions, tilt, base depth and control mounting remain open. Proposed 110 × 90 mm is only a placement-study envelope, not an accepted final size. Retain the existing two bank toggles, reset and power control; no new control functions or firmware changes.


## D043 — Rear serial and mini bus

Accepted: 2026-10-24, explicit user instruction. Serial connection and the 1×8 mini bus must be accessible from the back, alongside the three 1×12 full-port buses. Plan them on the rear-facing motherboard side with rear-cover access and cable clearance. Preserve the selected FT232RL cable/interface and existing electrical pin numbering; this does not select a new USB connector or close the deferred power/isolation circuit. Exact positions/orientations and cutouts await layout. See PCB-MECHANICAL.md.


## D044 — Eight 2 KB decode slots; retain existing RAM and ROM

Accepted: 2026-10-24, user requests the LS138/NAND slot concept applied to the existing plan, with additional RAM optional. Rewire the existing LS138 A/B/C to A11/A12/A13; enable with A15 high and A14 low. Place VIAs in Y6/Y7 (`$B000–$B7FF` / `$B800–$BFFF`) near ROM, leaving Y0–Y5 as six unpopulated 2 KB slots. Keep 32 KB RAM and four 16 KB ROM banks. No second decoder or extra SRAM is fitted.

Correct the supplied wiring: active-low HM62256 `/CE` is A15 directly, not inverted; LS138 pin 8 is GND and pin 7 is Y7. Existing LS00 gate D generates ROM `/CE` = NAND(A15,A14). Existing LS21 remains for PHI2/reset-qualified RAM writes, so the whole board is not described as having only two logic ICs. J2 becomes an internal 1×8 header for six spare selects/rails, not a full CPU expansion bus.

Supersedes D023/D036's 4 KB VIA mapping and first-decoder ROM-output combining only; manual bank controls, ROM layout, ABI 0.4.0, LCD workspace and case choices remain. Firmware, emulator, diagnostics, schematic and tests migrate together. The prior 47 KB/two-decoder discussion remains an unselected option; current slots allow at most 12 KB future extra RAM without further decode changes. See ADDRESS-DECODING.md.

## D045 — Isolated Pro Micro development bring-up

Accepted: 2026-10-25, user requests a minimal PlatformIO/Arduino environment in
`chip-tester/` and confirms the ATmega32U4 board is 16 MHz. Use the Pro Micro
16 MHz target; voltage is not measured and USB ID alone is not clock evidence.
Keep Python dependencies, downloaded AVR tools and build artifacts local and
ignored. Scope is onboard blink and USB serial only; chip-testing functionality
and external-chip setup are excluded. Stop for user action on system permissions,
physical interaction or USB reattachment. This does not change the 6502 hardware
contract or existing emulator workflow.
