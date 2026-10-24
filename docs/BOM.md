# Hardware BOM and open component decisions

Reconciled: 2026-10-24. This is the **current schematic planning BOM**, not a final purchasing list or physically validated assembly. All ICs must be DIP. The user owns the classic CPU/VIAs, SRAM/ROM, 74HC14, programmer and suitable capacitors; the 1 MHz active oscillator is purchased. Electrical condition and final fitted quantities remain to verify. No price/stock claim is made.

## Settled architecture and inventory

- MOS 6502, date code 0284, and two classic MOS 6522s from original Commodore 1541 drives. One VIA is photographed with lower marking 0284; second device detail remains to record. Photos are under `hardware/photos/` relative to this document.
- HM62256ALP-10 SRAM, 100 ns, wide DIP28. [Saved Hitachi sheet](hardware/datasheets/hm62256a.pdf) identifies this package/access time.
- Ten photographed W27C512-45Z devices; one 64 KB/45 ns wide DIP28 is used, others are spares. [Winbond sheet](https://media.digikey.com/pdf/Data%20Sheets/Winbond%20PDFs/W27C512.pdf).
- Fixed **1 MHz** with the purchased 5 V-assumed active oscillator. The speed choice is settled; no divider, selectable clock or new speed-grade decision is required.
- 32 KB RAM, four 16 KB ROM banks, 2 KB VIA blocks at `$B000`/`$B800`. Decode and serial pin migration are implemented in firmware/emulator. `$8020` is an unpopulated expansion address; software bank selection is retired.
- Manual bank toggles, separate hardware reset, power toggle and owned HC14 buffered RC reset. See [RESET.md](RESET.md).
- Through-hole PCB with socketed ICs facing the LCD; single-row peripheral headers on the rear-facing bottom. Larger board/bezel is allowed; **110 × 90 mm is a working placement-study envelope**, not final size. See [PCB-MECHANICAL.md](PCB-MECHANICAL.md) and [PCB-FIT.md](PCB-FIT.md).

## ICs, oscillator and sockets

| Qty | Part / schematic reference | Package and state |
| --- | --- | --- |
| 1 | MOS 6502, U1 | Owned; DIP40 socket |
| 1 | HM62256ALP-10, U2 | Owned; 100 ns, 600 mil DIP28 socket |
| 1 | W27C512-45Z, U3 | Owned; 64 KB, 45 ns, 600 mil DIP28 socket |
| 1 | 74LS138, U4 | Draft decoder; DIP16 socket |
| 1 | 74LS21, U5 | Reset-qualified RAM-write glue; other gate unused; DIP14 socket |
| 1 | 74LS00, U6 | ROM-select and read/write glue; DIP14 socket |
| 1 | 74HC14, U7 | Owned reset logic; DIP14 socket |
| 2 | MOS 6522, U8/U9 | Owned classic VIAs; DIP40 sockets |
| 1 optional | 74HC4511, U10 | Bank digit driver; DIP16 socket; actual digit remains to select |
| 1 | 1 MHz active oscillator, Y1 | Purchased; assume 5 V, half-size DIP8 four-lead footprint |

Sockets: **3 × DIP40, 2 × wide DIP28, 3 × DIP14, 1 × DIP16**, plus a second DIP16 if the bank driver is fitted. Oscillator socket is optional. Choose actual through-hole ordering variants. No socketed memory/CPU substitution or SMD conversion is implied.

## Passives and controls in the draft

| Qty | Component | Assignment / status |
| --- | --- | --- |
| 4 | 4.7 kΩ resistors | R1–R4 CPU signal pulls |
| 3 | 10 kΩ resistors | R5 reset charge; R7/R8 bank pulldowns |
| 1 | 1 kΩ resistor | R6 reset sense/discharge limiting |
| 1 | 1N4148 | D1 reset discharge; see RESET.md for orientation |
| 2 if needed | 4.7 kΩ resistors | R9/R10 I2C pull-ups; omit duplicate pulls if module already provides suitable values |
| 7 optional | 470 Ω resistors | R11–R17 bank digit segments; provisional pending actual display/current |
| 1 | Normally open reset pushbutton | Lower front panel; exact part/mounting open |
| 2 | Manual bank toggles | EEPROM A14/A15; lower front panel, exact parts/mounting open |
| 1 | Board power switch | Lower front panel; exact switch and USB-aware power path deferred to PCB design |

Capacitors are specified below. The current schematic has 11 core/entry 100 nF positions and one optional bank-driver bypass, a 47 µF bulk capacitor, reset 10 µF and optional LCD 10 µF. Reserve 15 ceramic bypass parts for planning; final power/isolation additions can change the fitted count.

## Headers, displays and expansion

| Qty | Item | Selected / open |
| --- | --- | --- |
| 3 | Full-port headers J6–J8 | **1×12**, 2.54 mm male through-hole; rear-facing bottom |
| 1 | Mini header J9 | **1×8**, 2.54 mm male through-hole; rear-facing bottom |
| 1 | LCD connection J10 | Four signals: +5 V/GND/SDA/SCL; actual module order/mating arrangement to confirm |
| 1 optional module | LCD2004 + PCF8574 backpack | Software mirror/dashboard implemented; actual model/address/mapping/outline unconfirmed |
| 1 optional | Common-cathode bank digit | Driven by U10 from toggle nets, consumes no VIA GPIO; physical digit/pinout open |
| 1 | FT232RL USB serial/power cable | Selected six-foot 5 V TTL cable, six-contact female end; rear-accessible serial/power header; actual pin order/current rating open |
| 1 | Internal expansion-select/test header J2 | 1×8 male; six spare selects + GND/+5 V, not a CPU address/data bus |
| As required | Controls, power and test connectors | Current J1–J5/J11–J19 include draft test/source/isolation-review provisions; not all are committed external connectors |
| Provision only | Removable 5 V Arduino-style SD module | Mini-bus routing/space reserved; module fitting, isolation and software deferred |

Full-port buses: VIA1 PB+CB, VIA2 PA+CA, VIA2 PB+CB. Mini bus: VIA1 PA4–PA7 + CA1/CA2. All include switched +5 V/GND. Serial is PA0 TX/PA1 RX; I2C is PA2 SDA/PA3 SCL. [PINOUT.md](PINOUT.md) defines the numbered signals. Keyboard design is deferred and does not claim these ports by default.

## Case and mechanical hardware

Printed case/front/base and removable back; custom standoffs, brass inserts and four long retaining screws. Mostly upright LCD leans backward; bank/reset/power controls sit below it. Retain the LCD-relative hole pattern while allowing motherboard/bezel growth. Exact angle, outline, supports, screw thread/length, insert type/location and spacer heights await placement/case review. Rear cutouts must allow fully mated DuPont connectors. The bank indicator's position is still a proposal.

## Decisions still needed before fabrication

Pre-placement coverage review: [SCHEMATIC-AUDIT.md](SCHEMATIC-AUDIT.md). The core parts are represented; power/serial closure, exact control/display parts and PCB mounting-hole/keepout details still affect final placement.

1. Full-BOM placement and routing envelope; final board outline and actual LCD mounting measurements. Reference LCD 98 × 60 mm / 93 × 55 mm hole centers does not freeze motherboard size.
2. Exact panel/board control parts, bank digit, rear connector locations, mated-cable clearance and enclosure stack.
3. PCB power/source/switch/USB off-state isolation, actual cable pin order/rating, load/inrush and board-end voltage. Draft J15/J16 serial links remain unresolved.
4. **Verify actual LCD 7-bit I2C address and backpack mapping.** `$27` and common expander wiring are development defaults; check pull-ups and module connector order.
5. Record second VIA/oscillator markings and physical condition; program/read back the W27C512 with the T48, then perform board bring-up.

The 1 MHz target, all-DIP construction, SRAM suffix, manual bank controls, single-row headers and lower control-panel location are settled. Keep the existing user-selected parts; unresolved design tasks do not require re-asking these choices.

## Selected clock source — purchased

Accepted by the user: **1.000 MHz active oscillator module, assumed 5 V**, from [AliExpress item 1005005522770275](https://www.aliexpress.com/item/1005005522770275.html) (`https://a.aliexpress.com/_mMNF62F`). Exact manufacturer/model is not shown by the listing. Purchase is confirmed; delivery/quantity/electrical operation have not been confirmed. Allocate one module on the board, using the half-size DIP-8 four-lead package shown in the supplied ECS-2100 sheet.

The board needs **no separate crystal, crystal oscillator amplifier, feedback/load network, frequency divider, or speed jumper**. Normal local power bypassing and the system's clock routing/reset design remain. Do not claim that the purchased oscillator is manufactured by ECS merely because that sheet is the chosen reference. The 5 V assumption is explicit user direction, not an independently verified listing specification.

Earlier salvaged-crystal, quartz-assortment/HCU04/divider and CTS full-size oscillator alternatives are superseded for this board. No need to purchase their extra parts. The source frequency and CPU target are both fixed at 1 MHz; firmware and emulator timing already match.

### Supplied ECS-2100 oscillator datasheet

User supplied a one-page image-only [ECS-2100 series datasheet](hardware/datasheets/ecs-2100-supplied.pdf), visually reviewed and retained in the project. This identifies a complete **HCMOS/TTL-compatible powered oscillator**, not a bare resonator. It is the selected mechanical/design reference; it does not independently establish that a generic AliExpress device is genuinely this manufacturer/series or supplied to these specifications. The user has explicitly authorized the 1 MHz/5 V assumption for planning; the exact delivered marking remains undocumented.

The supplied sheet specifies:

| Parameter | Specification |
| --- | --- |
| Frequency family range | 1.000–150.000 MHz; individual devices are fixed-frequency, not adjustable |
| Supply | 5.0 V ±0.25 V; optional 3.3 V version mentioned separately |
| Package | Half-size DIP-8 footprint with four physical leads, numbered 1/4/5/8 |
| Pin 1 | NC; leave unconnected for this specified part |
| Pin 4 | Ground |
| Pin 5 | Clock output |
| Pin 8 | +5 V |
| Duty cycle at 1 MHz | Table: 45–55% at 50% VDD |
| Rise/fall time | 5 ns maximum, 10–90% / 90–10% VDD |
| Output load | 10 TTL loads or 50 pF HCMOS in this frequency range |
| Output voltage | VOH ≥4.5 V at IOH=-16 mA; VOL ≤0.5 V at IOL=16 mA |
| Startup | Up to 10 ms |
| Supply current, 1–25 MHz | 17 mA typical, 25 mA maximum |

The user purchased the **1.000 MHz** option and directs us to assume **5 V**. The sheet's example `ECS-2100A-100` means **10.000 MHz**, not 1 MHz; do not order by a guessed suffix. A/B/C denote advertised frequency stability (100/50/25 ppm), not CPU speed. Read the drawing's bottom/top-view labels carefully when laying out the footprint.

For an actual matching 1 MHz device, no external oscillator amplifier or divider is needed. Allocate a local 100 nF bypass capacitor between supply and ground, check trace/load requirements and original MOS CPU clock input/routing, and hold CPU/VIA reset until the oscillator has started plus the chips' required reset timing. The module needs no enable wiring for the pinout shown (pin 1 is NC). Other oscillator families may use that position as enable: use their own datasheet. Power/reset timing and the actual supplied part still need hardware verification.


## Capacitor schedule — available from user stock

The user says to specify the recommended capacitors and assume stock is available. Capacitor availability is not an open question.

| Quantity | Value/type/rating | Assignment | Status |
| --- | --- | --- | --- |
| One per IC supply pair | **100 nF / 0.1 µF ceramic, ≥16 V**, typically marked `104` | CPU, both VIAs, SRAM, ROM, oscillator, decoder, glue, reset IC and display driver if fitted | Selected default; exact count after schematic |
| 1 | **47 µF aluminum electrolytic, ≥16 V** | Across board 5 V input and ground | Proposed initial bulk value; confirm with final source/load and inrush |
| 1 if needed | **10 µF aluminum electrolytic, ≥16 V** | LCD supply connector | Proposed local bulk if LCD fitted and existing module capacitance is insufficient |
| 1 | **10 µF electrolytic, ≥16 V** | RC/74HC14 reset timing | Separate from optional LCD bulk capacitor; validate actual delay |
| Circuit-dependent | Regulator-specific values | Any subsequently chosen regulator | Select from its datasheet at PCB stage |

Reserve **15 of the 100 nF parts** for assembly planning, not as the final fitted count. The six principal packages (CPU, two VIAs, SRAM, ROM, oscillator) need at least six; decoder, glue and reset ICs add to that, with peripherals as fitted. Add one at any separate power-entry/interface location required by the final design. For chips with multiple supply pairs, follow the device datasheet and bypass each pair as required.

Local ceramics connect in parallel between supply and ground, beside their supply connections with short leads/traces and a short return path. Bulk electrolytics are polarized: positive to +5 V, negative to ground. Values above are for the regulated 5 V rail, not an unspecified higher-voltage regulator input. They do not replace regulator-specific input/output capacitor requirements if a regulator is later chosen. The active oscillator needs no crystal load capacitors.

The 47 µF and optional 10 µF are practical draft selections, not calculated proof of power integrity. [Toshiba's logic decoupling guidance](https://toshiba.semicon-storage.com/us/semiconductor/knowledge/faq/logic_common/logic_common_06.html) gives 0.01–0.1 µF local decoupling and 10–100 µF board-level filtering as general ranges. Final power distribution, LCD load, source requirements and physical measurements will determine any adjustment.

## Selected USB serial and power interface

The user selects a six-foot cable described as genuine FT232RL in a USB-A plug with a six-way 0.1-inch female header. Advertised signals: TX, RX, RTS#, CTS#, VCC (+5 V) and GND, with **5 V TTL UART levels**. Exact brand/model and physical pin ordering are unspecified. This is a user-supplied description, not an independently verified manufacturer identification or purchase report.

Use this cable for both console and board power when connected to a PC; a generic USB brick supplies standalone power with no PC console connection. Cross adapter TX to board RX and adapter RX to board TX, connect grounds, and connect its +5 V supply to board power through the selected input arrangement. Hardware UART flow control is not currently used; configure the host accordingly. Do not assign colors or physical header pin numbers from a different vendor's cable. No logic inversion is required for the existing idle-high 8N1 console; EEPROM inversion options are capabilities, not requirements.

After the cable-current question, the user wrote "assume 500mv USB 2 standard to be safe." In context this is interpreted as **500 mA**, not 500 mV: the rail remains **5 V**. Adopt **500 mA total input current** as the explicit design assumption; this includes the USB converter and board, so 500 mA is not all available to the SBC. Allocate CPU, two classic VIAs, memory, oscillator, glue, LCD backlight, bank LEDs and expansion loads within that budget with headroom. Verify board-end voltage under load because the cable is six feet long.

This assumption does not establish the actual cable's rating or USB compliance. FTDI's own similar [TTL-232R-5V](https://ftdichip.com/products/ttl-232r-5v/) is rated **75 mA maximum power output**, but uses a different stated IC/package and is not identified as the user's exact cable. The [FT232R datasheet](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232R.pdf) distinguishes pre-configuration, configured and suspend power: USB 2.0's 500 mA high-power ceiling is not an unconditional allowance before enumeration or in suspend. A power brick has no PC enumeration; cable behavior must also allow standalone power. No measured supply capability or PC/brick behavior is claimed.

Engineering next: complete worst-case and typical current tables, account for interface use, source/cable drop, and define input protection/inrush and reset. The proposed 47 µF board bulk capacitor is subject to that inrush/input design, not an approved direct USB-port capacitance. Keep any future auxiliary power disconnected from cable VCC unless appropriate source selection/isolation is designed. No regulator, voltage-level shifter or second supply is added merely by default.


## Preliminary current estimate

[Power budget](POWER-BUDGET.md) estimates approximately **300 mA serial-only**, **400–500 mA with LCD/backlight and bank display**, including USB interface overhead and excluding external expansion loads. Conservative allocations round to **750 mA core / 1 A with displays**; these are mixed manufacturer-limit/engineering allowances, not measurements or a closed guaranteed worst case. Prefer a 5 V source rated 2 A and a verified ≥1 A board power path when choosing hardware. This is a recommendation pending user choice, not confirmation that the existing serial cable can carry it or that a PC USB 2.0 port supplies 1 A. The prior 500 mA assumption remains recorded but is insufficient for a conservative full-display budget. Finalize actual cable rating/architecture and measure board-end voltage before validating supply adequacy.


## Power-input options deferred to PCB design

Accepted user direction: design power options when the actual PCB is designed. Retain the selected FT232RL cable for the intended serial/power connection and the documented current estimates; do not require another adapter purchase or choose a second connector, regulator, source selector or protection circuit now. During PCB design, provide suitable input options for the measured/budgeted load and address source isolation, cable VCC connection, voltage drop, USB power states, inrush and protection. No assumption that separate sources may be directly paralleled, or that the existing cable is rated for the conservative full-board current, follows from this deferral.


## ROM programmer — identified

The user owns an **XGecu T48 (TL866-3G)** programmer. XGecu's T48 device list includes **W27C512 @DIP28**; [manufacturer list](https://www.xgecu.com/MiniPro/T48_List.txt) and [manufacturer-list mirror](https://pdf.direnc.net/upload/t48-universal-programmer-device-list.pdf), listed near PDF p. 270. The direct manufacturer endpoint was not accessible during review; the published mirrored list supplies the compatibility evidence. This is documented support, not a completed test of the user's unit/software or ROM chips.

Plan off-board erase/blank-check/program/verify of the complete `build/amc6502.bin` 64 KB image. Select the matching Winbond W27C512 DIP28 device profile and follow the programmer software's placement diagram and voltage algorithm; do not substitute a superficially similar memory part. Read back and compare all 65,536 bytes. No on-board programming connector or special adapter is added to the board BOM solely for this DIP28 ROM; confirm actual programmer instructions when using it. Host programming software/version and USB connection workflow can be documented when first flashing; no new software installation is implied by identifying the model.


## Scope and validation

The native schematic and 76-test emulator/ROM stage are implemented. No PCB routing, case CAD, physical flash or assembled-board validation is complete. SD/keyboard software remain deferred. Source documents above support component assumptions; actual part condition, wiring and power behavior require physical checks. See [STATUS.md](STATUS.md) for actual verification and [PLAN.md](PLAN.md) for next actions.

Chip-select revision (2026-10-24): one existing LS138 now provides eight 2 KB slots, with VIAs on Y6/Y7; ROM select moves to existing LS00 gate D. The LS21 is retained for write qualification. No second SRAM/decoder/socket/bypass is added. J2 grows from 1×3 to 1×8. Extra RAM/6116 population stays optional and unimplemented. See [ADDRESS-DECODING.md](ADDRESS-DECODING.md).

Optional 6116 inventory is pending the user’s planned 2026-10-25 check. Empty upgrade sockets are an option, not a selected BOM quantity. Record exact DIP package/marking before adding socket or bypass footprints and include their area in the placement study.
