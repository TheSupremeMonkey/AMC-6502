# BOM and schematic audit before placement

Reviewed: 2026-10-24. Scope: current native schematic/exported netlist, BOM, reset circuit and accepted enclosure plan. This is a logical coverage/readiness audit, not a routed-board or electrical sign-off.

## Conclusion

The core CPU/memory/VIA computer is represented. No additional core-support IC is established as missing by this audit. The BOM is **not yet final**: the power/serial interface is deliberately unresolved, several physical parts have no selected model, and mounting hardware has not become PCB hole/keepout placement. A rough placement study can proceed with explicit reservations; final placement/routing should wait for the items below.

## Covered in the current draft

- Original NMOS 6502, two classic MOS 6522s, 32 KB SRAM and the four-bank 64 KB ROM, with DIP sockets.
- 74LS138 decode, 74LS21/74LS00 memory control, fixed 1 MHz active oscillator and owned HC14 buffered RC reset.
- CPU IRQ/NMI/RDY/SO pulls, shared VIA IRQ, unused logic inputs tied to defined levels, unused outputs explicitly unconnected.
- Two bank-switch input pulls and external toggle connections, reset button connection and board power-switch connection.
- Local bypass, bulk and reset capacitors; no missing crystal circuit/divider is implied.
- Three 1×12 full-port buses, 1×8 mini bus, LCD connection and serial/power header. All external buses and serial are rear-accessible in the planned layout; controls go below the LCD.
- I2C pull-up positions, optional bank-driver IC, segment resistors and an external digit connection.

## Close before final placement/routing

| Item | Present state / required action | Placement consequence |
| --- | --- | --- |
| Power input and switch | Select the final source arrangement and close USB/off-state serial back-power paths; cable current/pin order remain unverified | Any added interface/isolation/protection parts must have space and footprints |
| Serial TX/RX | J15 separates FT_TX from SER_RX; J16 separates SER_TX from FT_RX. These are review-link headers, not a completed isolation circuit | Resolve how the signal paths are connected/isolated before routing; do not claim the unbridged draft is a working physical serial connection |
| Controls | Two bank toggles, reset and power are in the BOM but no exact switch/button models are selected | Choose panel-wired versus board-mounted and physical envelopes for the lower control panel; current schematic uses headers |
| LCD | Four-wire connection is provided; actual module/backpack, dimensions, address, pin mapping and pull-ups remain unconfirmed | Define connector/keepout/cable envelope; verify actual 7-bit address and mapping at bring-up. `$27` is a development assumption |
| Bank digit | Optional U10 and seven resistors/header are shown; exact common-cathode digit/model is not selected | Decide whether it is fitted and how it mounts/connects; confirm resistor/current values against the chosen digit |
| Mechanical mounting | Four long screws, inserts and custom spacers are planned; final screw/hole/keepout dimensions are open | Add four appropriate PCB mounting-hole footprints and standoff/copper/component keepouts in the board design; retain the LCD-relative pattern |
| Rear connections | 1×12/1×8 geometry is selected; serial cable order and mated housing dimensions are not verified | Plan fully mated DuPont/serial connector clearance and rear-cover cutouts, plus rear-readable pin labels |

The original MOS VIA port input loading matters when selecting I2C pull-ups. R9/R10 are candidates, not instructions to add duplicate pulls in parallel with the backpack. Check actual module resistors and the ACK-low load before finalizing them. References: [MOS 1982 catalogue, printed p. 2-63](https://bitsavers.trailing-edge.com/components/mosTechnology/_dataBooks/1982_MOS_Technology_Data_Catalog.pdf), [NXP PCF8574/PCF8574A datasheet](https://www.nxp.com/docs/en/data-sheet/PCF8574_PCF8574A.pdf).

## Useful conveniences, not new requirements

A switched-power indicator LED/resistor and accessible +5 V/GND test pads would help bring-up. Clock/reset/IRQ/SYNC already have debug-header access. No indicator or extra interface IC is added by this audit; choose conveniences deliberately rather than treating them as missing essentials. Keep optional SD at the reserved mini-bus/module provision and keyboard implementation deferred.

## Verification and next step

`make schematic-check` was rerun: KiCad ERC reports **zero violations**, 26 key pin connections pass, and PDF/netlist exports succeed. The netlist also shows the known serial link separation above; zero ERC does not close that design choice. No emulator/firmware changes or physical tests were performed for this audit.

Recommended order: close power/serial design, select/control the physical component envelopes, then perform the 110 × 90 mm working-envelope placement study with mounting and rear-connector keepouts. Exact LCD address testing and firmware flashing can occur at bring-up, but the module's mechanical envelope must be reserved during placement.
