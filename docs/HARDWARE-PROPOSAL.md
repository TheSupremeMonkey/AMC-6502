> Historical proposal. Current implementation uses eight 2 KB slots at `$8000–$BFFF`, with VIA1 `$B000`/VIA2 `$B800`, serial PA0 TX/PA1 RX and manual bank toggles/reset. `$8020` is unpopulated expansion; LCD is implemented. Use [ADDRESS-DECODING.md](ADDRESS-DECODING.md) and [MACHINE.md](MACHINE.md) for the current contract.


# Proposed 4 KB hardware decoding architecture

Received 2026-10-23. This records the user's hardware proposal and conflicts found against the working firmware. Clarified by the user: keep the existing four 16 KB ROM banks, each split into an 8 KB personality and 8 KB shared kernel. The 4 KB decoder granularity applies to chip selects, not ROM bank size. This decode/layout direction is accepted. The user subsequently chose two bank toggles plus separate hardware reset; I/O/firmware migration and detailed circuit wiring remain pending. Existing ROM/emulator behavior is unchanged pending that migration.

## Proposed decode and pins

MOS 6502 at fixed **1 MHz** (the user superseded the original 1–2 MHz proposal), with HM62256 32 KB RAM. CPU A15 drives RAM active-low /CE directly; A15 high enables a 74LS138/74HC138 whose A/B/C inputs receive CPU A12/A13/A14. Decoder outputs are active-low:

| Output | CPU addresses | Proposed assignment |
| --- | --- | --- |
| Y0 | `$8000–$8FFF` | VIA 1 |
| Y1 | `$9000–$9FFF` | VIA 2 |
| Y2 | `$A000–$AFFF` | Expansion |
| Y3 | `$B000–$BFFF` | Expansion |
| Y4 | `$C000–$CFFF` | ROM personality, first 4 KB |
| Y5 | `$D000–$DFFF` | ROM personality, second 4 KB |
| Y6 | `$E000–$EFFF` | Shared ROM kernel, first 4 KB |
| Y7 | `$F000–$FFFF` | Shared ROM kernel, second 4 KB |

With only A0–A3 connected to each VIA's register-select inputs, its 16 registers repeat 256 times throughout its 4 KB block. Consequently `$8020` becomes a VIA 1 register alias, not a separate bank selector. ROM /CE can be formed as the logical AND of active-low Y4, Y5, Y6, and Y7; decoder outputs must not be tied together. RAM write timing and ROM output-enable/read qualification remain circuit design work. LS/HC family choice requires actual voltage-level/timing checks with the selected classic chips.

Proposed VIA 1 Port A: PA0 TX, PA1 RX, PA2/PA3 bank bits, PA4 SDA, PA5 SCL, PA6/PA7 spare. CA1 falling-edge bank button IRQ. Port B remains available for keyboard/peripheral use. The bank bits also feed a 74HC4511; its remaining BCD inputs/control pins and the display wiring need defined levels. The LCD2004 uses a PCF8574 backpack, with firmware reading the current bank tag and updating telemetry; this LCD behavior is not implemented yet.

## Clarified ROM layout

Four **16 KB** banks fill the **64 KB W27C512**. Each maps a personality at `$C000–$DFFF` and the shared kernel at `$E000–$FFFF`, exactly as in the current build. Payload entry stays `$C000`; existing shared ABI addresses need no relocation. CPU A0–A13 feed EEPROM A0–A13; the two bank-select signals feed EEPROM A14/A15. The source of those bank signals is still unresolved; the original proposal's EEPROM A13/A14 bank wiring is superseded.

The initial 8 KB bank window, 6 KB payload, 2 KB kernel, `$E000` payload entry, and 32 KB used EEPROM footprint are superseded by this clarification. Current BASIC (7,895 bytes) still fits its 8 KB allocation. Decoder output granularity does not require separate physical ROM chips or separate banks for each 4 KB output.

The original proposal also requested a 16-byte identity at `$FFE0–$FFEF`. That is separate from bank size and remains a proposed metadata change; the implemented 32-byte identity at `$FFC0–$FFDF` remains in place until explicitly migrated. CPU vectors remain `$FFFA–$FFFF`.

## Conflicts requiring a decision

1. **BASIC capacity — resolved.** Keep the existing 8 KB payload and 8 KB shared kernel in each 16 KB bank. No BASIC replacement, RAM-loading scheme, or ABI relocation is needed.
2. **Bank selection and reset.** Existing behavior is select plus full CPU/VIA reset with a persistent external selector. VIA reset makes its ports inputs, so direct PA2/PA3 bank drive cannot retain that state by itself. A CA1 interrupt is software-controlled and does not itself reset the CPU/peripherals. Existing ROM code normally masks IRQ, and current IRQ dispatch does not implement a bank-button handler. Decide between persistent external latch plus full reset and VIA-controlled switching plus software reinitialization; the latter changes the accepted reset contract. Physical reset/power-on bank levels also need definition.
3. **Shared Port A ownership.** Existing TX is PA1 and RX PA0, opposite this proposal. Current TX code writes whole-port values 0/2 and initialization sets DDRA=2. It must be rewritten to preserve PA2–PA5, use safe output shadows, and initialize pins in a safe sequence. Otherwise transmitting would change the active ROM bank and disturb I2C. Bank transitions must execute entirely from mirrored code, with defined IRQ/NMI handling.
4. **I/O migration.** Keep the current 64 KB image, linker regions, and ABI. Update VIA 2 from `$8010` to `$9000`, implement 4 KB VIA aliases, and replace the conflicting `$8020` selector once its new interface is chosen. Rewrite pin-dependent drivers and diagnostics with corresponding tests. Metadata migration is separate; LCD remains unimplemented.
5. **Software bank access.** BASIC `POKE 32800,...`, Woz `$8020`, and the provisional selector register cease to work under this decode. A supported firmware entry or other interface must replace them, consistent with the chosen reset policy. No emulator-only selector trap should remain at `$8020`.

The 4 KB decode and existing ROM layout are compatible. Bank/reset behavior and replacement software selector must be resolved before replacing the working I/O implementation. Metadata and pin changes can then be implemented together, without leaving a partially migrated ROM.

References: [TI HC138 datasheet](https://www.ti.com/tw/lit/gpn/sn74hc138), [Winbond W27C512 datasheet](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/900/W27C512.pdf), and [Rockwell 6522 datasheet](https://www.princeton.edu/~mae412/HANDOUTS/Datasheets/6522.pdf).

## Option 1 candidate discrete hardware — not yet selected

To support independent button advance and software selection with full CPU/VIA reset, a candidate implementation uses a 74LS161A parallel-load counter as the bank-state register. Its low two outputs select EEPROM A14/A15 and feed the bank display. Software supplies a parallel bank value; a debounced button requests one increment. Counter clear belongs to power-on initialization, not ordinary CPU/VIA reset. The unused upper counter outputs are not connected to EEPROM address inputs.

Additional functions: address/read/write decode in an expansion block; a tri-state readback buffer such as 74LS244; RC/Schmitt button conditioning such as 74LS14; a reset pulse generator such as 74LS123; and synchronous request/priority/reset sequencing using suitable gates/flip-flops (for example 74LS74). Exact package count, control equations, clock edge, RC values, power-on reset source, and bus timing need a schematic. A counter plus one-shot alone is not a complete safe design. Use one controlled clocking/sequencing arrangement rather than simply ORing asynchronous button and bus strobes onto the counter clock. The power-on source must initialize bank 0 and hold CPU/VIA reset appropriately; a separate reset supervisor is an option.

Counter load/count requests must produce one update and a sufficiently long CPU/VIA reset, with the bank stable before reset release and no unintended memory writes during transition. Readback must only drive the CPU bus on decoded reads. Existing Y2 at `$A000–$AFFF` could host the register, but exact address/aliasing is not selected. This option frees VIA PA2/PA3; serial and I2C no longer need to preserve ROM selection bits on that port. The display still needs its 4511, appropriate display and resistors, independent of the bank-state/control circuitry.

Part references: [TI SN74LS161A](https://www.ti.com/product/SN74LS161A), [TI SN74LS244](https://www.ti.com/product/SN74LS244), [TI SN74123/LS123 family](https://www.ti.com/product/SN74123). These are candidate functions and parts, not an approved BOM or validated circuit.


## Latest simplification under consideration: manual bank toggles

The user proposed and then explicitly confirmed two toggles on EEPROM A14/A15 and a separate hardware reset button. This replaces software switching; earlier electronic-selector options are superseded. With it, bank bits are independent of the VIAs and survive CPU/VIA reset; operating procedure is hold RESET, set toggles, allow contacts to settle, release RESET. Defined address-input levels and a proper reset circuit are still required. Firmware-controlled selection, the `$8020` selector, numeric bank-changing menus, and select/reset semantics would be retired or redesigned; no emulator-only substitute should disguise their absence. Firmware-readable bank state would need spare inputs or per-bank metadata, not an assumed writable selector. VIA PA2/PA3 and CA1 would be available. The counter/latch hardware above is an alternative, not part of the manual-toggle BOM. See [BOM and open decisions](BOM.md).

The bank/reset conflicts and electronic options above are historical alternatives: user decision D028 selects manual toggles. No replacement writable selector is needed. Retire software-switching assumptions and migrate firmware bank identity queries without an emulator-only register. See [BOM](BOM.md).
