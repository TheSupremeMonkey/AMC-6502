#!/usr/bin/env python3
"""Paced Intel HEX sender; stdlib-only serial and pin-level emulator transports."""
import argparse
from pathlib import Path
import select
import sys
import termios
import time
import os


def record(address, data=b'', kind=0):
    body = bytes((len(data), address >> 8, address & 255, kind)) + data
    return ':' + (body + bytes((-sum(body) & 255,))).hex().upper()


def validate(lines):
    result = []
    ended = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ended or not line.startswith(':'):
            raise ValueError('Expected Intel HEX records ending with exactly one EOF')
        try:
            raw = bytes.fromhex(line[1:])
        except ValueError:
            raise ValueError('Invalid hexadecimal record') from None
        if len(raw) < 5 or len(line) != 1 + 2*len(raw) or len(raw) != raw[0]+5 or sum(raw) & 255:
            raise ValueError('Invalid record length or checksum')
        count, hi, lo, kind = raw[:4]
        address = hi*256+lo
        if kind == 1 and count == 0 and address == 0:
            ended = True
        elif kind != 0 or count > 16 or not 0x300 <= address < 0x7F80 or address+count > 0x7F80:
            raise ValueError('Only 0..16-byte RAM records at $0300-$7F7F and EOF are supported')
        result.append(line.upper().encode('ascii'))
    if not ended:
        raise ValueError('Missing EOF record')
    return result


def send(transport, records):
    transport.expect(b'HEX READY\r\n')
    for line in records:
        for char in line:
            data = bytes((char,))
            transport.write(data)
            transport.expect(data)  # echo acknowledges readiness for the next character
        transport.write(b'\r')
        transport.expect(b'\r\n')
        transport.expect(b'DONE\r\n' if line == b':00000001FF' else b'OK\r\n')


class EmulatorTransport:
    def __init__(self, image):
        # Import from repository even when invoked as scripts/send_hex.py.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from emulator.machine import Machine
        self.machine = Machine(image)
        self.machine.select_bank(3)
        self.machine.run(1000000)
        self.offset = len(self.machine.bus.serial.output)
        self.write(b'L')

    def write(self, data):
        self.machine.bus.serial.feed(data)

    def expect(self, expected):
        # Every receive is bounded in emulated instructions, independent of host speed.
        for _ in range(200):
            output = bytes(self.machine.bus.serial.output[self.offset:])
            if len(output) >= len(expected):
                if not output.startswith(expected):
                    raise ValueError(f'Expected {expected!r}, received {output!r}')
                self.offset += len(expected)
                return
            self.machine.run(1000)
        raise TimeoutError(f'Emulator waiting for {expected!r}')


class SerialTransport:
    def __init__(self, port):
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        self.original = termios.tcgetattr(self.fd)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[4] = attrs[5] = termios.B9600
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIFLUSH)

    def close(self):
        termios.tcsetattr(self.fd, termios.TCSANOW, self.original)
        os.close(self.fd)

    def write(self, data):
        os.write(self.fd, data)

    def expect(self, expected):
        deadline = time.monotonic()+10
        received = bytearray()
        while len(received) < len(expected):
            timeout = deadline-time.monotonic()
            if timeout <= 0 or not select.select([self.fd], [], [], timeout)[0]:
                raise TimeoutError(f'Serial waiting for {expected!r}')
            received.extend(os.read(self.fd, len(expected)-len(received)))
        if received != expected:
            raise ValueError(f'Expected {expected!r}, received {bytes(received)!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--emulator', action='store_true')
    target.add_argument('--port', help='POSIX serial device; leave target at diagnostics menu first')
    parser.add_argument('--rom', type=Path, default=Path(__file__).resolve().parents[1]/'build/amc6502.bin')
    args = parser.parse_args()
    transport = None
    try:
        records = validate(args.file.read_text(encoding='ascii').splitlines())
        transport = EmulatorTransport(args.rom.read_bytes()) if args.emulator else SerialTransport(args.port)
        if isinstance(transport, SerialTransport):
            transport.write(b'L')
        send(transport, records)
        print(f'Transfer complete: {len(records)-1} data record(s); program not started.')
    finally:
        if isinstance(transport, SerialTransport):
            transport.close()


if __name__ == '__main__':
    main()
