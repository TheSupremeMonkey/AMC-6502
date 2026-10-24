# LCD2004 console and dashboard

The shared NMOS 6502 firmware drives a 20×4 HD44780-compatible display through a PCF8574 backpack on VIA1 PA2 SDA / PA3 SCL. Serial stays on PA0 TX / PA1 RX. Both modes use real firmware writes, I2C acknowledgements and LCD enable strobes; the emulator does not copy serial capture into the display.

## Modes and terminal use

Run `make run`, then:

```text
:lcd mirror
:lcd
:lcd dashboard
:lcd
:lcd off
```

`:lcd` inspects the four rows without advancing time or changing device state. A mode command writes the documented firmware request byte and resumes a bounded slice if paused. Firmware applies the request at a console output/input service point. Arbitrary application code that never calls console services must call `FW_LCD_MODE` itself; the host does not force the CPU into a service routine.

- **Off (0):** cold-start default; no LCD probing or I2C traffic until requested. Switching off an initialized display blanks it and turns off the backlight.
- **Mirror (1):** every character sent through `FW_COUT` also goes to a scrolling 20×4 console. Printable 7-bit text wraps at 20 columns; CR returns to column zero, LF starts the next row, CR/LF works as one line break, and advancing past the bottom scrolls up. BS/DEL moves the cursor left within the row; subsequent text overwrites. Form feed clears. Other control characters are ignored on the LCD. This is a small character console, not an ANSI terminal or a serial receive monitor.
- **Dashboard (2):** rows show `AMC-6502 STATUS`, the active ROM bank description (truncated to 20 characters), nominal CPU/RAM information, and an application status line. Console output continues on serial without overwriting the dashboard. `FW_LCD_STATUS` updates only the last row, truncating/padding to 20 characters (control characters terminate the status text). Bank 3 diagnostics reports testing and the final PASS/FAIL summary there when rerun.

Warm CPU/bank resets retain the mode request when a two-byte RAM marker is valid, then firmware reinitializes the display and updates the bank. This is retained RAM, not EEPROM configuration or a physical mode switch. The external LCD has no connection to CPU reset; its contents remain until firmware reinitializes it. Deterministic emulator cold RAM starts with LCD off; arbitrary hardware power-on RAM and final cold-boot configuration still need bring-up validation.

## Firmware interface (API 0.4.0)

Include `firmware/include/fw.inc`. All LCD services are synchronous and non-reentrant. Call with IRQ disabled or an application policy that excludes interfering serial/I2C/Port A handlers. D/I and X/Y are preserved; flags other than returned carry are unspecified.

| Vector | Service | Input / result |
| --- | --- | --- |
| `$E124` | `FW_LCD_MODE` | A=0 off,1 mirror,2 dashboard. C=0 success; C=1 invalid mode or I2C NACK. A clobbered |
| `$E127` | `FW_LCD_CLEAR` | Clear current LCD and mirror cursor/buffer; A preserved. C=1 if off or I2C failure |
| `$E12A` | `FW_LCD_STATUS` | A/Y low/high pointer to NUL text; truncate/pad to 20 columns on dashboard row 4. A preserved. C=1 unless dashboard active and writes succeed |

```asm
    lda #2
    jsr FW_LCD_MODE
    bcs no_display
    lda #<status
    ldy #>status
    jsr FW_LCD_STATUS
    ; ...
status: .byte "PUMP: RUN",0
```

BASIC can request mirror with `POKE 765,1`, dashboard with `POKE 765,2`, and off with `POKE 765,0`. `$02FD` is a RAM request mailbox, not a device register. Applying a change takes effect on the next console service. Reset clears/reinitializes the appropriate driver state; no software bank switch is introduced.

## Address and backpack assumptions — verify on hardware

- [ ] **Identify the actual 7-bit LCD backpack address before physical testing.** `$27` is only the development default. Check PCF8574 versus PCF8574A and A0–A2 straps. Do not confuse the 7-bit address `$27` with the transmitted write byte `$4E`.
- [ ] Verify backpack mapping: development assumption P0=RS, P1=RW, P2=E, P3=active-high backlight, P4–P7=LCD D4–D7. A different layout requires adapting the driver and model.
- [ ] Verify pull-ups, rise time, module connector pin order and display contrast/backlight on the actual assembly.

Firmware address is `LCD_ADDRESS` in `firmware/include/lcd.inc`; rebuild after changing it. Python `Machine(..., lcd_address=0x27, lcd_present=True)` configures the modeled backpack independently, allowing wrong-address and absent-device tests. No address scan is done at boot. The first NACK disables further automatic retries and leaves serial usable; request a mode again to retry.

The driver uses low output latches and VIA direction changes to drive low or release SDA/SCL. It preserves serial/mini-bus latches and direction bits via `FW_PORTA_SHADOW`. The model follows write transactions only; PCF8574 reads, clock stretching/arbitration, CGRAM glyphs, display shifts and analog timing are not implemented. LCD command/data writes have deterministic busy delays. Firmware uses conservative startup/clear waits and the 4-bit initialization sequence, with RW low; it does not read the busy flag.

References: [NXP PCF8574/PCF8574A datasheet](https://www.nxp.com/docs/en/data-sheet/PCF8574_PCF8574A.pdf), [Hitachi HD44780U datasheet](https://cdn-shop.adafruit.com/datasheets/HD44780.pdf). These define the device protocols; they do not establish the wiring of the user's unknown backpack.

## RAM and timing costs

Reserve **`$7F80–$7FFF` (128 bytes)** for the 80-character scroll buffer, driver scratch and warm-reset marker, plus ZP `$F2–$F3` and request byte `$02FD`. This reservation applies even with LCD off, keeping one firmware contract. Physical RAM is still 32 KB. BASIC's automatic probe and explicit memory-size path cap at exclusive `$7F80`; user RAM and serial uploads end at `$7F7F`. Diagnostics excludes the LCD workspace from its restoring scan. Woz can deliberately edit all RAM and must respect these reservations.

LCD output is blocking and slower than serial. A bounded terminal slice may stop partway through a long mirrored report; use `:continue` or `:run` to finish. Scrolling redraws all 80 characters. LCD work finishes before transmitting each serial character so an echo-paced uploader receives its echo after display work. Unpaced incoming serial during LCD updates can still be lost: this is software serial, with no background receiver. Dashboard updates should be application-driven at useful events; there is no fabricated CPU-register telemetry or automatic uptime timer.

`make test` includes assembled-firmware tests for both modes, scrolling/control characters, dashboard independence, status padding/truncation, mode validation, wrong/absent addresses, pin ownership, warm bank reset, BASIC RAM protection and inert host inspection, alongside existing serial/API/loader regressions.

A generated two-mode transcript is saved at `build/lcd-demo.txt`. The dashboard sample comes from actual bank 3 diagnostics; the mirror sample is emitted through shared COUT to both serial pins and LCD firmware.
