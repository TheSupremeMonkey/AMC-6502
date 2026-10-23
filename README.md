# AMC-6502 (AstroMonkey Micro Computer)

The **AMC-6502 (AstroMonkey Micro Computer)** is a modular, programmable 6502 single-board computer designed to operate both as a PC-tethered development tool and as an autonomous, standalone "cyberdeck."

## Technical Specifications

### Hardware Core

* **CPU:** W65C02S running at 1 MHz (configurable to 2, 4, or 8 MHz via clock divider).
* **Clock Generation:** 16 MHz primary oscillator routed through a 74HC393 ripple counter for flexible clock division.
* **RAM:** 32 KB SRAM (`$0000–$7FFF`).
* **Upper Memory Space:** 32 KB (`$8000–$FFFF`) allocated to system I/O and bank-switched ROM.
* **I/O Controllers:** Dual W65C22 Versatile Interface Adapters (VIA #1 and VIA #2).
* **ROM:** 64 KB Winbond W27C512 EEPROM operating via an 8 KB hardware bank-switched window (`$E000–$FFFF`).
* **Power & Data Interface:**
  * USB-to-TTL 5V Serial Adapter (serves as primary data interface and main power rail).
  * Auxiliary 5V DC power header for tetherless operation.

### Display & Front Panel

* **System Dashboard:** LCD2004 (20x4 character display) driven via an I2C backpack for real-time telemetry and active bank names.
* **Hardware Bank Display:** 7-segment display driven directly by hardware from the ROM bank selection pins ($PA_2, PA_3$) via a 74HC4511 BCD decoder (displays `0`–`3` instantly without software overhead).
* **Input Controls:** Front-panel tactile switch connected to VIA #1 $\text{CA}_1$ for edge-triggered interrupt-driven ROM bank cycling.

## System Memory Map

| Address Range | Size | Allocation | Function |
| ----- | ----- | ----- | ----- |
| `$0000–$7FFF` | 32 KB | System RAM | Zero Page, Stack, User RAM, System Buffers |
| `$8000–$800F` | 16 B | VIA #1 | System Controls, Bit-Bang Serial, Bank Control, LCD I2C |
| `$8010–$801F` | 16 B | VIA #2 | Dedicated Hardware & General I/O Expansion |
| `$8020–$DFFF` | ~24 KB | Decoding Reserve | Reserved / Unused System I/O |
| `$E000–$FFFF` | 8 KB | EEPROM Window | **Bank-Switched ROM Area (4 x 8 KB Banks)** |

## EEPROM Banking Architecture

The upper 8 KB address space (`$E000–$FFFF`) dynamically maps to one of four 8 KB banks inside the W27C512 EEPROM, driven by output pins $PA_2$ and $PA_3$ on VIA #1.

```
       W27C512 EEPROM (64 KB Total)
+----------------------------------------+
| Bank 0 (8 KB) : Microsoft BASIC        | ---> Mapped to $E000–$FFFF
+----------------------------------------+
| Bank 1 (8 KB) : Custom Monitor / Woz   | ---> Mapped to $E000–$FFFF
+----------------------------------------+
| Bank 2 (8 KB) : Standalone Cyberdeck OS| ---> Mapped to $E000–$FFFF
+----------------------------------------+
| Bank 3 (8 KB) : Diagnostic Suite       | ---> Mapped to $E000–$FFFF
+----------------------------------------+
```

### Bank Layout & Mirrored High Kernel

Each 8 KB bank is strictly divided into two functional regions:

1. **Lower Area (`$E000–$F7FF`, ~6 KB):**
   * Unique payload per bank (e.g., Microsoft BASIC, Monitor Shell, Standalone Keyboard OS).
   * Shares a standardized base entry point at `$E000` across all banks.
2. **Shared High Kernel (`$F800–$FFFF`, ~2 KB):**
   * **Mirrored across all 4 banks** to prevent CPU crashes during live bank swaps.
   * Contains hardware I/O drivers (Bit-Bang Serial, I2C LCD driver).
   * Houses the unified jump vector table (e.g., `COUT` at `$EE00`, `CIN` at `$EE03`).
   * Contains the interrupt-driven bank-switching routine.
   * **Bank Metadata:** Addresses `$FFE0–$FFEF` hold a fixed 16-byte null-terminated ASCII string (e.g., `"MICROSOFT BASIC"`, `"CYBERDECK OS  "`) displayed on the LCD dashboard during bank switches.
   * **CPU Vectors:** Hardcoded vectors at `$FFFA–$FFFF` (`NMI`, `RESET`, `IRQ/BRK`).

## Hardware Peripheral Pinout & Expansion Headers

The system breaks out a total of **4 8-bit parallel ports (32 I/O lines)** across its dual VIAs. Three full 8-bit ports remain completely uncommitted for modular expansion, with all signals exposed as clean 3-pin clusters (`Signal`, `+5V`, `GND`).

### VIA #1 (`$8000–$800F`) — System Controller & Primary Display

* **Port A ($PA_0–PA_7$):**
  * `$PA_0`: Serial Receive ($RX$)
  * `$PA_1`: Serial Transmit ($TX$)
  * `$PA_2`: ROM Bank Select Bit 0 (also wired to 74HC4511 BCD $A_0$)
  * `$PA_3`: ROM Bank Select Bit 1 (also wired to 74HC4511 BCD $A_1$)
  * `$PA_4`: I2C SDA (LCD2004 Dashboard Data line)
  * `$PA_5`: I2C SCL (LCD2004 Dashboard Clock line)
  * `$PA_6–PA_7`: Spare I/O / Status LEDs
  * $\text{CA}_1$: Debounced pushbutton input (triggers falling-edge hardware interrupt for bank swapping)
* **Port B ($PB_0–PB_7$):**
  * **Broken out for I/O Expansion:** 8x 3-pin headers (`Signal`, `+5V`, `GND`).
  * Used for scanning a matrix keyboard in Cyberdeck mode or user-defined peripherals.

### VIA #2 (`$8010–$801F`) — Dual Expansion Controller

* **Port A ($PA_0–PA_7$):**
  * **Broken out for I/O Expansion:** 8x 3-pin headers (`Signal`, `+5V`, `GND`).
  * Uncommitted 8-bit general-purpose parallel bus with full handshake lines ($\text{CA}_1$, $\text{CA}_2$).
* **Port B ($PB_0–PB_7$):**
  * **Broken out for I/O Expansion:** 8x 3-pin headers (`Signal`, `+5V`, `GND`).
  * Uncommitted 8-bit general-purpose parallel bus with full handshake lines ($\text{CB}_1$, $\text{CB}_2$).

## Operating Modes

1. **Development Tool Mode (PC-Tethered):**
   * Powered and interfaced over USB-to-TTL serial adapter.
   * Terminal interaction using PC console via unified `COUT` bit-bang vectoring.
   * LCD dashboard displays real-time execution states ($PC$, $A$, $X$, $Y$, Status Flags).
2. **Autonomous Cyberdeck Mode (Standalone):**
   * Powered via 5V DC power jack or USB battery bank.
   * Key matrix connected directly to VIA #1 Port B headers.
   * Switch to Bank 2 (Cyberdeck OS) using the tactile bank button; interactive text renders to the LCD screen.

## Software & Emulation Workflow

Development follows a software-first approach prior to PCB assembly:

1. **Compilation:** Assemble 6502 code using `ca65` or `vasm`.
2. **Emulation:** Test system binaries inside a custom Python test harness (`emulator/sbc_emu.py`) that models the memory bus, VIA registers, bit-bang serial out, I2C LCD buffer, and bank switching.
3. **Flashing:** Program the finalized 64 KB image containing all four banks onto the W27C512 via a USB EEPROM programmer (e.g., TL866II Plus).