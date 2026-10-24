"""Assembled API calls exercise actual shared firmware and serial pins."""
from pathlib import Path
import unittest
from emulator.machine import Machine

ROOT = Path(__file__).resolve().parents[1]


class FirmwareApiTests(unittest.TestCase):
    def machine(self, mode=0, bank=0, maximum=16):
        image = (ROOT / 'build/amc6502.bin').read_bytes()
        payload = (ROOT / 'build/abi-test.bin').read_bytes()
        image = b''.join(payload + image[b*0x4000+0x2000:(b+1)*0x4000] for b in range(4))
        m = Machine(image)
        if bank:
            m.select_bank(bank)
        m.bus[0x200] = mode
        m.bus[0x201] = maximum
        return m

    def output(self, m):
        self.assertEqual(m.bus.serial.framing_errors, 0)
        description = m.bus.rom[m.bus.bank*0x4000+0x3FC0:m.bus.bank*0x4000+0x3FE0].split(b'\0')[0]
        return bytes(m.bus.serial.output).split(description + b'\r\n', 1)[1]

    def test_print_hex_version_and_bank_queries_in_every_bank(self):
        for bank in range(4):
            with self.subTest(bank=bank):
                m = self.machine(bank=bank)
                m.run(250000)
                self.assertEqual(m.bus[0x20F], 0x42)
                self.assertEqual(self.output(m), b'ABI READY: AB1234\r\n')
                self.assertEqual(m.bus.ram[0x300:0x303], m.bus.ram[0x303:0x306])
                self.assertFalse(m.bus[0x306] & 1)
                self.assertEqual(m.bus.ram[0x307:0x30A], bytes((0xAB, 0x37, 0x6B)))
                self.assertEqual(m.bus.ram[0x30A:0x30D], bytes((0x34, 0x9A, 0x12)))
                self.assertTrue(m.bus[0x315] & m.cpu.DECIMAL)  # hex formatting preserves D
                self.assertEqual(m.bus.ram[0x30D:0x310], bytes((0, 4, 0)))
                self.assertEqual(m.bus[0x310], bank)
                self.assertEqual(m.bus.ram[0x313:0x315], bytes((4, 0)))

    def test_puts_crosses_page_and_bounds_unterminated_strings(self):
        for data, expected, failure in ((b'PAGE CROSSING\0', b'PAGE CROSSING', False),
                                        (b'A'*256+b'Z\0', b'A'*256, True)):
            m = self.machine(mode=3)
            m.bus[0x202], m.bus[0x203] = 0xF8, 3
            m.bus.ram[0x3F8:0x3F8+len(data)] = data
            m.run(400000)
            self.assertEqual(m.bus[0x20F], 0x42)
            self.assertEqual(self.output(m), expected)
            self.assertEqual(bool(m.bus[0x207] & 1), failure)
            self.assertEqual(m.bus.ram[0x204:0x207], bytes((0xF8, 0x5A, 3)))

    def test_line_editing_backspace_delete_and_register_contract(self):
        m = self.machine(mode=1)
        m.bus[0x27F] = 0xA5
        m.run(125000)
        m.bus.serial.feed(b'\bAB\bC\x7fDE\r')
        m.run(100000)
        self.assertEqual(m.bus[0x20F], 0x42)
        self.assertEqual(m.bus.ram[0x280:0x284], b'ADE\0')
        self.assertEqual(m.bus.ram[0x204:0x207], bytes((0, 3, 0x6B)))
        self.assertFalse(m.bus[0x207] & 1)
        self.assertEqual(m.bus[0x27F], 0xA5)
        self.assertEqual(self.output(m), b'AB\b \bC\b \bDE\r\n')

    def test_line_capacity_and_null_termination(self):
        m = self.machine(mode=1, maximum=111)
        m.bus.ram[0x280:0x2F0] = b'\xCC'*112
        m.run(125000)
        m.bus.serial.feed(b'X'*120+b'\r')
        m.run(500000)
        self.assertEqual(m.bus[0x20F], 0x42)
        self.assertEqual(m.bus.ram[0x280:0x2F0], b'X'*111+b'\0')
        self.assertEqual(m.bus[0x205], 111)
        self.assertEqual(self.output(m), b'X'*111+b'\x07'*9+b'\r\n')

    def test_invalid_line_limit_returns_without_input_or_buffer_write(self):
        for maximum in (0, 112, 255):
            m = self.machine(mode=1, maximum=maximum)
            m.bus.ram[0x280:0x2F0] = b'\xCC'*112
            m.run(125000)
            self.assertEqual(m.bus[0x20F], 0x42)
            self.assertEqual(m.bus.ram[0x204:0x207], bytes((1, 0, 0x6B)))
            self.assertTrue(m.bus[0x207] & 1)
            self.assertEqual(m.bus.ram[0x280:0x2F0], b'\xCC'*112)
            self.assertEqual(self.output(m), b'')

    def test_line_crlf_does_not_insert_an_empty_second_line(self):
        m = self.machine(mode=4)
        m.run(125000)
        m.bus.serial.feed(b'ONE\r\nTWO\n')
        m.run(100000)
        self.assertEqual(m.bus[0x20F], 0x42)
        self.assertEqual(m.bus.ram[0x400:0x404], b'ONE\0')
        self.assertEqual(m.bus.ram[0x280:0x284], b'TWO\0')
        self.assertEqual(self.output(m), b'ONE\r\nTWO\r\n')

    def test_poll_is_idle_nonblocking_and_distinguishes_nul(self):
        for value in (0, 0x41, 0x7F):
            with self.subTest(value=value):
                m = self.machine(mode=2)
                m.run(125000)
                self.assertEqual(m.bus[0x20F], 0)
                self.assertEqual(m.bus[0x20E], 0x11)
                self.assertEqual(m.bus.ram[0x204:0x207], bytes((0, 0x37, 0x6B)))
                self.assertFalse(m.bus[0x207] & 1)
                m.bus.serial.feed(bytes((value,)))
                m.run(10000)
                self.assertEqual(m.bus[0x20F], 0x42)
                self.assertEqual(m.bus.ram[0x204:0x207], bytes((value, 0x37, 0x6B)))
                self.assertTrue(m.bus[0x207] & 1)
                self.assertEqual(self.output(m), b'')

    def test_poll_reception_across_start_bit_phases(self):
        for phase in range(0, 104, 8):
            with self.subTest(phase=phase):
                m = self.machine(mode=2)
                m.run(125000)
                m.bus.serial.feed(b'U')
                start, value = m.bus.serial.frames[0]
                m.bus.serial.frames[0] = (start + phase, value)
                m.run(10000)
                self.assertEqual(m.bus[0x20F], 0x42)
                self.assertEqual(m.bus[0x204], 0x55)
                self.assertTrue(m.bus[0x207] & 1)
