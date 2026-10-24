# Reserved VIA 1 pin allocation: serial, I2C and mini bus

Accepted pin reservation: serial on PA0/PA1, I2C on PA2/PA3 and a four-line mini bus on PA4–PA7, with SD SPI as its planned optional use. Include the bus/SD connection provision in PCB design; defer SD software testing and implementation. This does not claim modules are fitted or firmware has been migrated. VIA 1 target block is `$B000–$B7FF`; its 16 registers repeat throughout the block.

| Signal | MOS 6522 DIP pin | Planned function | Direction |
| --- | --- | --- | --- |
| PA0 | 2 | Serial TX to adapter RX | Output, idle high |
| PA1 | 3 | Serial RX from adapter TX | Input |
| PA2 | 4 | I2C SDA to LCD backpack | Bidirectional, low or released |
| PA3 | 5 | I2C SCL to LCD backpack | Low or released; readable |
| PA4 | 6 | Mini bus line 0; optional SD SCK | Application-defined; SD output when enabled |
| PA5 | 7 | Mini bus line 1; optional SD MOSI/DI | Application-defined; SD output when enabled |
| PA6 | 8 | Mini bus line 2; optional SD MISO/DO | Application-defined; SD input when enabled |
| PA7 | 9 | Mini bus line 3; optional SD /CS | Application-defined; SD output when enabled |
| PB0–PB7 | 10–17 | Uncommitted full port; potential keyboard/peripheral use | Application-defined |
| CA1 / CA2 | 40 / 39 | Available; no bank-button assignment | Application-defined |
| CB1 / CB2 | 18 / 19 | Available, subject to future Port B/keyboard interface | Application-defined |

Power: pin 20 +5 V, pin 1 ground; reset pin 34 joins the shared reset net. The bank display connects to EEPROM bank-toggle nets, not PA2/PA3. All eight Port A bits are reserved in this plan; a later profile jumper/card-detect input needs a separately chosen input path. Do not silently allocate a mini-bus bit for it.

The LCD backpack connection uses just **+5 V, GND, SDA, SCL**. Reserve 4.7 kΩ pull-ups to +5 V on SDA/SCL as initial candidates only if equivalent pull-ups are not already on the module; verify actual bus capacitance, rise time and classic VIA input-current loading before finalizing. A PCF8574 backpack moves LCD parallel signaling and typically backlight control onto the expander; no extra VIA RS/E/data/backlight pin is planned. Exact backpack address and mapping remain to identify. Do not confuse expander P0–P7 quasi-bidirectional LCD outputs with the VIA's SDA/SCL bus wiring.

For I2C, set the selected VIA output latch bits to zero, then use direction bits to drive low or release as input. Read SDA for ACK; never force a high against a slave's low. Preserve other Port A latch/direction bits during serial and I2C writes. Existing serial driver whole-port writes are unsuitable for sharing the port unchanged. LCD availability remains independent of keyboard enablement; scanning a keyboard consumes no pins from this table until its interface is chosen.

**Implemented:** emulator/ROM serial uses PA0 TX and PA1 RX. LCD/I2C support is implemented; SD remains deferred. Firmware uses the shared `$02FC` output-latch shadow to preserve unrelated bits; future drivers must maintain it.

References: [MOS 1982 catalogue, printed p. 2-50 / PDF p. 61](https://bitsavers.trailing-edge.com/components/mosTechnology/_dataBooks/1982_MOS_Technology_Data_Catalog.pdf) for the DIP pin numbers; [NXP PCF8574/PCF8574A](https://www.nxp.com/docs/en/data-sheet/PCF8574_PCF8574A.pdf) for I2C/backpack expander characteristics. These were reviewed; actual wiring and firmware coexistence have not been tested.


## Optional bus ownership

PA4–PA7 are a reusable four-line GPIO mini bus, not a permanently configured SPI controller. Leave them as inputs/unclaimed until application or optional SD software takes ownership. Default firmware must not scan for SD or toggle these pins merely because a connector exists. Serial and I2C routines must preserve their latch and direction state. Switching away from SD use also needs electrical disconnection or a verified non-interfering module; a software-disabled module can still load or drive a shared line.

Expose the four signals, +5 V and GND, with provision for a removable 5 V Arduino-style SPI SD module. Exact header order, module footprint/mounting and any disconnect jumpers are PCB choices. The motherboard-side bus is in the 5 V system domain; a selected module must provide its own appropriate regulation/translation for the SD card. See [SD-CARD.md](SD-CARD.md). SD driver, card model and filesystem remain deferred.

## Accepted expansion grouping

The mini bus includes VIA1 CA1/CA2. This supersedes the earlier proposal to put those two controls on I/O 1 and permits three identical full-port headers.

| Connection | GPIO | Associated controls | Power | Minimum contacts |
| --- | --- | --- | --- | --- |
| Mini bus | VIA1 PA4–PA7 | VIA1 CA1/CA2 (DIP 40/39) | +5 V/GND | 8 |
| I/O 1 | VIA1 PB0–PB7 | VIA1 CB1/CB2 | +5 V/GND | 12 |
| I/O 2 | VIA2 PA0–PA7 | VIA2 CA1/CA2 | +5 V/GND | 12 |
| I/O 3 | VIA2 PB0–PB7 | VIA2 CB1/CB2 | +5 V/GND | 12 |

This routes each control pair with its corresponding port, retains every peripheral signal and allows the three full-port connectors to have identical relative signal/power positions. The KiCad draft uses 1×12 0.1-inch headers for full ports and 1×8 for the mini bus. Standard 2.54 mm (0.1-inch) through-hole pin headers are selected: three 12-pin full-port headers and one 8-pin mini header. The single-row 1×12/1×8 arrangement is selected; placement/orientation are PCB choices.

For the full-port headers, generic relative labels could be D0–D7, C1, C2, +5 V and GND, mapped to the corresponding PA/PB and CA/CB signals above. C1 is the associated control input; C2 has configurable control functions. They are identically arranged signals, not identical software capabilities in every mode. VIA1 CA1/CA2 still belong logically to its whole Port A, shared with serial/I2C; PCR/ACR settings and control interrupts must be coordinated with system firmware.

SD SPI itself still needs only the four PA4–PA7 lines plus power/ground. CA1/CA2 are extra exposed facilities for later devices, not an extra SD requirement or permission to claim them in default firmware. A six-wire SD module would connect to the appropriate six positions with the two extras unused. Changing grouping is connector routing only; no new VIA or decode logic is needed. The previous I/O 1 extra-control grouping is superseded.


Draft numbered connections: full-port pins 1–8 = D0–D7, 9 = C1, 10 = C2, 11 = GND, 12 = switched +5 V. Mini pins 1–4 = PA4–PA7, 5 = CA1, 6 = CA2, 7 = GND, 8 = switched +5 V. External load limits and off-state isolation remain part of PCB power review. CA1/CB1 are inputs; CA2/CB2 are configurable control signals. Keyboard ownership remains optional and unassigned.

The selected **single-row** headers accept standard 2.54 mm DuPont leads. Number pins consecutively along the row and mark pin 1, +5 V and GND on the PCB silkscreen. Full-port pins 11/12 remain GND/+5 V; mini pins 7/8 remain GND/+5 V.

LCD driver and write-side backpack emulation are implemented; see [LCD.md](LCD.md). Verify the actual backpack 7-bit I2C address and pin mapping before hardware testing; `$27` is a development default.

Peripheral headers mount on the motherboard bottom, facing the case back and its cutouts. Keep these electrical pin assignments; add rear-readable pin-1/signal/power labels. Check mated DuPont housing/cable clearance in the case stack. See [PCB-MECHANICAL.md](PCB-MECHANICAL.md).

Rear-access requirement (2026-10-24): J6–J8 full ports, J9 mini bus and the serial/power cable connection must all be accessible from the back, with rear-facing motherboard placement and cover cutouts. Actual FT232 cable order still needs verification.
