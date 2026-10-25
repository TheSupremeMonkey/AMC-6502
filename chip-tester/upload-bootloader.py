#!/usr/bin/env python3
"""Wait up to 60 seconds for the 16 MHz Pro Micro bootloader, then upload."""

from pathlib import Path
import subprocess
import sys
import time

from serial.tools import list_ports


def main():
    project = Path(__file__).resolve().parent
    firmware = project / ".pio/build/promicro16/firmware.hex"
    tools = project / ".platformio/packages/tool-avrdude"
    if not firmware.is_file() or not (tools / "avrdude").is_file():
        sys.exit("Run ./pio run -e promicro16 first to prepare firmware/tools.")

    bootloader_ids = {(0x1B4F, 0x9205), (0x2341, 0x0037)}
    print("Waiting 60 seconds for bootloader USB 1b4f:9205 or 2341:0037. "
          "Double-reset now.",
          flush=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        ports = [port.device for port in list_ports.comports()
                 if (port.vid, port.pid) in bootloader_ids]
        if len(ports) > 1:
            sys.exit("Multiple Pro Micro bootloaders found; disconnect extras.")
        if ports:
            print(f"Bootloader found at {ports[0]}; uploading.", flush=True)
            # Match PlatformIO's AVR109 upload; retain default readback checking.
            result = subprocess.run([
                str(tools / "avrdude"), "-C", str(tools / "avrdude.conf"),
                "-p", "atmega32u4", "-c", "avr109", "-P", ports[0],
                "-b", "57600", "-D", "-U", f"flash:w:{firmware}:i",
            ], timeout=30)
            return result.returncode
        time.sleep(0.1)
    sys.exit("Bootloader did not appear in WSL within 60 seconds; no upload.")


if __name__ == "__main__":
    sys.exit(main())
