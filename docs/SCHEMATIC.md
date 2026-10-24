# KiCad schematic draft

Open [AMC-6502.kicad_pro](../hardware/kicad/AMC-6502.kicad_pro) in KiCad 9. The editable native schematic has a root overview and six subsystem sheets: CPU/memory, decode/clock, reset/controls, VIAs/I/O, power/serial, and optional bank display. Project-local symbols are included; standard KiCad DIP/socket footprints are used. All ICs are DIP. No PCB layout has been created.

Ubuntu tooling is optional for firmware work:

```sh
sudo apt install --no-install-recommends kicad kicad-symbols kicad-footprints
make schematic-check
```

This exports `build/schematic/AMC-6502.pdf`, an XML netlist and an ERC JSON report. Generated files stay out of Git. The checker also verifies key reset, memory-select, bank, serial and connector pins. KiCad 9.0.8 reports zero ERC violations on the initial draft. ERC does not prove original-chip timing, voltage compatibility, circuit startup or physical wiring. Edit native sources directly; they are the design source of truth.

## Draft circuit

RAM `/CE` is CPU A15 directly. U6 gate D produces ROM `/CE` = NAND(A15,A14). U4 LS138 takes A11/A12/A13 on pins 1/2/3, A14 on active-low enable pin 4, ground on pin 5 and A15 on pin 6. It decodes `$8000–$BFFF` into eight 2 KB slots; Y6/Y7 select VIA1 at `$B000` and VIA2 at `$B800`. Pins 8/7 are ground/Y7 respectively. See [ADDRESS-DECODING.md](ADDRESS-DECODING.md).

U5 LS21 remains for WRITE_OK = PHI2 AND READ_N AND RESET_N; U6 inverts that for RAM `/WE` and provides READ_N = NOT(R/W). U5 gate A and U6 gate C are unused with inputs grounded and outputs unconnected. HC14 reset and oscillator are unchanged. No second decoder or extra SRAM is added. J2 becomes an internal 1×8 select/test header for six spare selects plus GND/+5 V, not a complete memory-expansion bus.

Memory is HM62256ALP-10 (100 ns, wide DIP28) and W27C512-45Z. Three full-port 1×12 headers and a mini 1×8 header implement the accepted grouping in [PINOUT.md](PINOUT.md). Standard 2.54 mm through-hole pin headers are selected; the single-row 1×12/1×8 arrangements are selected.

## Review before PCB or purchasing

- Panel controls are represented by headers; panel versus board mounting remains open. Hold reset while changing bank toggles.
- Power input/source selection and USB off-state isolation are unresolved. J15/J16 serial links remain open pending that design. A VCC switch alone does not establish isolation from powered UART signals. Input connectors and FTDI pin order are provisional; verify the actual cable.
- Optional 74HC4511 drives an external common-cathode digit through provisional 470 Ω resistors. Exact display, current and physical pinout remain open. LCD connector order, backpack mapping/pull-ups and module mounting also need confirmation.
- Mini bus reserves optional SD signals and CA1/CA2; software and exact module remain deferred.
- Check clock/reset startup, original MOS chip input/output loading, memory access paths and maximum supply load before layout approval. No physical operation is claimed.

The emulator/ROM now follows the accepted map, manual banking and serial pinout. Physical programming and board operation remain unverified.

Current schematic migration (2026-10-24): VIA1 `$B000–$B7FF`, VIA2 `$B800–$BFFF`, repeated 16-register aliases; PA0 TX/PA1 RX. Manual bank toggles plus reset replace software selection. `$E106` returns carry set; `$8020` is unpopulated expansion. See [ROM switching](ROM-SWITCHING.md). LCD mirror/dashboard support is implemented; see [LCD guide](LCD.md).

Layout direction: socketed ICs face the LCD; three full-port buses, mini bus and serial/power connection face the rear cover. Controls sit below the backward-leaning LCD. Larger motherboard allowed; 110 × 90 mm is the working study envelope. See [mechanical plan](PCB-MECHANICAL.md). Schematic symbols/footprints do not implement PCB-side placement.

Pre-placement audit: [SCHEMATIC-AUDIT.md](SCHEMATIC-AUDIT.md). Core coverage is present; resolve power/serial review links, exact control/display envelopes and PCB mounting-hole/keepout details before freezing placement.

Current static verification also evaluates the exported LS138/LS00/LS21 connections across 256 address/read/write/reset combinations. See [ADDRESS-DECODING.md](ADDRESS-DECODING.md).
