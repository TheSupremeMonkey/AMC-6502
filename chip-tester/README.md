# Pro Micro bring-up

Onboard blink and USB serial only; no chip tests or external-chip connections.
The user confirmed **16 MHz**. The PlatformIO target is `sparkfun_promicro16`
(5 V/16 MHz); supply voltage has not been measured. USB IDs alone do not
establish clock speed.

## Build in the VS Code WSL terminal

```sh
cd ~/projects/AMC-6502/chip-tester
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./pio --version
./pio run -e promicro16
```

The first three setup commands are only needed on a fresh checkout.
Python 3 with `venv` is required; verified on Ubuntu 26.04.1 / Python 3.14.4.
PlatformIO Core 6.2.0 and Python dependencies are pinned in `requirements.txt`.
`platformio.ini` pins AVR platform 5.3.0, Arduino AVR 5.4.0, AVR GCC package
1.70300.191015 (GCC 7.3.0), and avrdude 1.60300.200527.
The `pio` wrapper keeps tools in `.platformio/`, Python in `.venv/`, and
builds in `.pio/`, all ignored. First setup/build needs internet. No Arduino
IDE, VS Code extension, external libraries, or system-wide tool install is needed.

## Serial access

`/dev/ttyACM0` uses `root:dialout`, mode `0660`. User `brad` has already been
added to `dialout` with authorized `sudo usermod -aG dialout brad`.
Reconnect the VS Code WSL session if `id -nG` still omits `dialout`.
Check `test -r /dev/ttyACM0 && test -w /dev/ttyACM0` before upload.
During setup, `sudo -n -u brad` refreshed groups for commands while running
the uploader as **brad**, not root. Do not run PlatformIO as root.

## WSL USB setup

This compatible board has different identities in sketch and bootloader mode:

| Mode | USB ID | Observed port |
| --- | --- | --- |
| Running sketch | `1b4f:9206` | WSL `/dev/ttyACM0`, Windows COM3 |
| Arduino Micro bootloader | `2341:0037` | WSL `/dev/ttyACM0`, Windows COM4 |

Current Windows bus is `1-9`. In ordinary **Windows PowerShell**, keep this
running during upload and monitor use:

```powershell
usbipd list
usbipd attach --wsl --busid 1-9 --auto-attach
```

The sketch was already shared. The user also created this bootloader policy
in **Administrator PowerShell**; do not repeat it on this installation:

```powershell
usbipd policy add --effect allow --operation AutoBind --busid 1-9 --hardware-id 2341:0037
```

Its GUID is `30cbcc80-3b61-44a5-8cd0-ec6c829c67c3`. It automatically shares only
this bootloader ID at this port. An earlier SparkFun-only rule
(`1178ef7c-4959-43c8-a7df-50409372abd5`, ID `1b4f:9205`) was insufficient.
Use `usbipd policy remove --guid <GUID>` as Administrator to remove a rule.
If moving USB ports, recheck the bus ID and adjust the policy/attach command.
On a fresh setup, sharing an unshared sketch also needs Administrator
`usbipd bind --busid <BUSID>`. Stop for user action on reattachment or permissions.

## Upload — automatic reset verified

Close other serial monitors. Leave the PowerShell auto-attach loop running.

```sh
./pio run -e promicro16 -t upload --upload-port /dev/ttyACM0
```

This performs the 1200-baud reset automatically. Re-upload was verified without
touching RST: PlatformIO reported `SUCCESS` in 6.21 seconds and avrdude verified
all 4,244 flash bytes. Serial banner and heartbeats resumed after reattachment.
Keep auto-attach running and retain the `2341:0037` AutoBind rule above. Select
the actual serial port if its number changes. No bootloader replacement is needed.

### Manual-reset fallback

If automatic upload fails to find the bootloader, the previously verified
manual workflow remains available:

```sh
./pio run -e promicro16
.venv/bin/python upload-bootloader.py
```

At `Double-reset now`, briefly connect **RST to GND twice quickly**, then release.
The helper waits up to 60 seconds for the bootloader, then uses project-local
avrdude to upload the PlatformIO-built HEX and verify flash readback. It accepts
`2341:0037` and the SparkFun default `1b4f:9205`, refuses multiple matching
boards, and does not reset again. Success is `4244 bytes of flash verified`
(for this firmware) and exit status zero. The existing sketch is replaced;
the bootloader is retained.

## Monitor and expected behavior

After the sketch reattaches:

```sh
./pio device list
./pio device monitor --port /dev/ttyACM0 --baud 115200
```

Use the current port from `device list`; numbering can change. DTR is enabled
by `platformio.ini`. Exit with Ctrl-C. On opening the monitor:

```text
AMC-6502 chip-tester bring-up; configured F_CPU=16000000 Hz; blink/USB serial only
alive 1
alive 2
```

The banner repeats when the monitor reconnects; the counter continues until
reset. `F_CPU` is the compiled setting, not a clock measurement. 115200 is a USB
CDC monitor setting, not a physical UART bit rate. The RX activity LED alternates
every 500 ms without waiting for a monitor; USB receive activity may briefly
override it. TX may flicker with output. The power LED remains lit. The code
uses onboard RX LED macros (PB0), not pin 13, and leaves external headers unconfigured.

## Verified 2026-10-25

- Local PlatformIO works; Python dependency check passed.
- 16 MHz build passed: **4,244 bytes flash, 165 bytes RAM**.
- Manual upload from WSL succeeded with auto-attach and the `2341:0037` policy.
  avrdude reported ATmega32U4 signature `0x1e9587` and verified all 4,244 bytes.
- Subsequent standard PlatformIO re-upload succeeded with automatic reset,
  no physical interaction: all 4,244 bytes verified, `SUCCESS` in 6.21 seconds.
  Serial banner and three heartbeats were verified again afterward.
- USB serial banner and `alive 1` through `alive 6` captured at `/dev/ttyACM0`;
  measured heartbeat intervals were approximately **1.001–1.002 seconds**.
- User confirmed the onboard LED blinking. No chip-testing functionality added.

References: [PlatformIO board](https://docs.platformio.org/en/latest/boards/atmelavr/sparkfun_promicro16.html),
[SparkFun reset guidance](https://learn.sparkfun.com/tutorials/pro-micro--fio-v3-hookup-guide/troubleshooting-and-faq),
[WSL USB](https://learn.microsoft.com/en-us/windows/wsl/connect-usb),
[usbipd policies](https://github.com/dorssel/usbipd-win/wiki/New-design:-policies).
