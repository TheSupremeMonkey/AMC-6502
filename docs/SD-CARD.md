# Reserved mini bus and deferred SD storage

Status: user accepts reserving **PA4–PA7 as a four-line mini bus**, including PCB connection/space provision for a **5 V Arduino-style SPI SD module**. SD testing, firmware and emulator implementation are explicitly deferred. No specific module/card purchase or working storage is claimed.

## Accepted VIA 1 reservation

Reserve I2C on PA2/PA3 and the mini bus on PA4–PA7. When SD is enabled, use these SPI assignments:

| Signal | MOS 6522 DIP pin | Proposed use |
| --- | --- | --- |
| PA0 | 2 | Serial TX |
| PA1 | 3 | Serial RX |
| PA2 | 4 | I2C SDA |
| PA3 | 5 | I2C SCL |
| PA4 | 6 | SD SCK/CLK, output |
| PA5 | 7 | SD MOSI/DI, output |
| PA6 | 8 | SD MISO/DO, input |
| PA7 | 9 | SD /CS, output, inactive high |

This is an accepted pin reservation, not a requirement to initialize SPI at boot. All four mini-bus pins remain generic GPIO until a driver/application claims them. It uses all of VIA 1 Port A but none of its Port B or the other VIA's parallel ports. A profile input/card-detect signal has no reserved Port A spare in this version; do not silently allocate extra pins. No card detect/write-protect pin is required for the first rudimentary interface; removable-card and error behavior must be defined in software.

## Module requirements

Use a module with **5 V supply input, onboard 3.3 V regulation and appropriate SPI logic-level conversion**. A bare socket or a regulator-only 5 V module is not equivalent. The card itself uses the 3.3 V domain. Check regulator/card peak-current capability, SPI output loading, whether MISO is direct 3.3 V or translated, and /CS startup pull-ups/idle levels. Choose a level-shifting input stage whose guaranteed high/low thresholds are compatible with classic MOS VIA outputs, rather than assuming every Arduino-compatible module is equally suitable.

A [documented example](https://www.adafruit.com/product/254) provides onboard regulation and level shifting; [SparkFun's level-shifting module documentation](https://learn.sparkfun.com/tutorials/microsd-breakout-with-level-shifter-hookup-guide/hardware-overview) illustrates an alternative that also translates return signals. These establish module types, not a required vendor or compatibility approval of an unidentified module. No additional motherboard regulator/level-shifter is assumed if the selected module already provides the required functions.

The connector needs +5 V, ground, SCK, MOSI, MISO and /CS. Exact order/footprint follows the selected module, not generic wire colors. Keep /CS inactive during reset and other peripheral activity. Review power-off/USB back-power paths along with the existing PCB action item.

## Firmware and emulator implications

Bit-banging requires no dedicated SPI controller or CPU address block, but it is firmware work. Shared Port A drivers must preserve other output-latch and direction bits: SPI must not disturb serial/I2C, and serial whole-port writes must be replaced. Avoid naïve read/modify/write of port pins as a substitute for owned latch shadows. I2C uses low-or-release signaling; SPI is a distinct interface with its own directions and chip select.

At the fixed 1 MHz CPU clock, SPI throughput and initialization clocks need an explicit instruction-cycle budget and real card checks before claiming broad card compatibility. No performance figure, guaranteed supported card list or FAT implementation is established. The console is unbuffered bit-banged serial; do not promise simultaneous incoming serial capture during long SD operations.

Suggested software order: initialize/identify one card and report errors with bounded timeouts; read one 512-byte sector; then decide raw-sector versus a filesystem/file loader. Reuse suitable existing classic-6502 or small filesystem code where practical, checking licensing and ROM/RAM budget. Allocate a sector buffer explicitly without trampling BASIC/application RAM. Filesystem compatibility, writes and BASIC save/load are separate scope decisions; start read-only if that meets the initial use.

An emulator implementation must consume actual modeled VIA SPI pins and return card responses with bounded emulated time, not trap firmware calls or copy host files directly into RAM.

## BOM and power impact

PCB scope: reserve the four signals plus +5 V/GND on a mini-bus/SD connector and allow space/mounting for a removable module. Module/card fitting is optional; no exact purchased module, regulator or capacitor quantity is selected yet. Preserve general bus access and avoid permanent SD circuitry that prevents reuse. Firmware leaves unused bus pins as inputs and performs no SD probing. Provide electrical disconnection or verify module loading/tri-state behavior before another peripheral shares the wires. Update the power budget for actual card/module peak activity before PCB input design; the existing 300 mA core /400–500 mA display estimates **exclude SD storage and external expansion**.

The accepted motherboard mini header has eight contacts: four GPIO, VIA1 CA1/CA2, +5 V and GND. SD SPI uses six of these; the two control lines are optional expansion facilities. See [PINOUT.md](PINOUT.md).
