"""Real ROM loader exercised over modeled serial pins; no RAM upload shortcuts."""
from pathlib import Path
import unittest
from scripts.send_hex import EmulatorTransport, record, send, validate

ROOT = Path(__file__).resolve().parents[1]


class LoaderTests(unittest.TestCase):
    def transport(self):
        return EmulatorTransport((ROOT/'build/amc6502.bin').read_bytes())

    def line(self, t, text, response):
        for char in text.encode('ascii'):
            t.write(bytes((char,)))
            t.expect(bytes((char,)))
        t.write(b'\r')
        t.expect(b'\r\n'+response+b'\r\n')

    def test_transfer_boundaries_and_execute_uploaded_classic_code(self):
        t = self.transport()
        # LDA #$42; STA $0400; JMP $0305 -- NMOS instructions only.
        code = bytes.fromhex('A9428D00044C0503')
        lines = validate([record(0x300, code), record(0x7F70, bytes(range(16))), record(0, kind=1)])
        send(t, lines)
        m = t.machine
        self.assertEqual(m.bus.ram[0x300:0x308], code)
        self.assertEqual(m.bus.ram[0x7F70:0x7F80], bytes(range(16)))
        self.assertEqual(m.bus[0x400], 0)  # upload never executes
        m.cpu.pc = 0x300
        m.run(20)
        self.assertEqual(m.bus[0x400], 0x42)
        self.assertEqual(m.bus.serial.framing_errors, 0)

    def test_rejected_records_do_not_write_and_recovery_works(self):
        t = self.transport()
        t.expect(b'HEX READY\r\n')
        m = t.machine
        m.bus.ram[0x300:0x310] = b'Q'*16
        m.bus.ram[0x7F70:0x7F80] = b'Z'*16
        bad = [record(0x300, b'BAD')[:-2]+'00', record(0x2FF, b'XY'),
               record(0x7F7F, b'XY'), record(0x7F80, b'XY'), record(0x7FF0, b'XY'), record(0x8000, b'XY'), record(0xFFFF, b'XY'),
               record(0x300, b'X'*17), record(0, b'\0\1', kind=4),
               ':GG00000000', record(0x300, b'X')+'X', record(1, kind=1),
               record(0x300, b'X')+'X'*300]
        for text in bad:
            with self.subTest(text=text[:50]):
                self.line(t, text, b'ERR')
                self.assertEqual(m.bus.ram[0x300:0x310], b'Q'*16)
                self.assertEqual(m.bus.ram[0x7F70:0x7F80], b'Z'*16)
                self.assertEqual(m.bus.bank, 3)
        self.line(t, record(0x300, b'OK'), b'OK')
        self.line(t, record(0, kind=1), b'DONE')
        self.assertEqual(m.bus.ram[0x300:0x302], b'OK')

    def test_abort_returns_to_diagnostic_menu(self):
        t = self.transport()
        t.expect(b'HEX READY\r\n')
        t.write(b'\x1b')
        t.expect(b'ABORT\r\n')
        t.expect(b'R to rerun / L load HEX\r\n')

    def test_sender_preflight_rejects_invalid_files(self):
        for lines in ([], [record(0x300,b'A')], [record(0,kind=1)]*2,
                      [record(0x200,b'A'),record(0,kind=1)],
                      [':010300004100',record(0,kind=1)]):
            with self.subTest(lines=lines), self.assertRaises(ValueError):
                validate(lines)

    def test_posix_transport_over_pseudo_terminal(self):
        import os
        import termios
        import select
        from concurrent.futures import ThreadPoolExecutor
        from scripts.send_hex import SerialTransport
        master, slave = os.openpty()
        before = termios.tcgetattr(slave)
        transport = SerialTransport(os.ttyname(slave))
        records = validate([record(0x300, b'A'), record(0, kind=1)])

        def read_byte():
            if not select.select([master], [], [], 2)[0]:
                raise TimeoutError("Pseudo terminal peer timed out")
            return os.read(master, 1)

        def target():
            os.write(master, b'HEX READY\r\n')
            for line in records:
                for char in line:
                    self.assertEqual(read_byte(), bytes((char,)))
                    os.write(master, bytes((char,)))
                self.assertEqual(read_byte(), b'\r')
                os.write(master, b'\r\n'+(b'DONE' if line == b':00000001FF' else b'OK')+b'\r\n')

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(target)
                send(transport, records)
                future.result(timeout=2)
        finally:
            transport.close()
            self.assertEqual(termios.tcgetattr(slave), before)
            os.close(master)
            os.close(slave)
