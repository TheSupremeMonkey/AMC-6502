"""Assembled LCD firmware through VIA open-drain I2C, PCF8574 and LCD pins."""
from copy import deepcopy
from pathlib import Path
import unittest
from emulator.machine import Machine
from emulator.terminal import Terminal

ROM = Path(__file__).resolve().parents[1] / 'build/amc6502.bin'


class LCDTests(unittest.TestCase):
    def machine(self, **kwargs):
        m = Machine(ROM.read_bytes(), bank=1, **kwargs)
        m.run(150000)
        return m

    def call(self, m, vector, a=0, y=0, budget=400000):
        # JSR a public firmware vector; capture carry and completion in user RAM.
        code = bytes((0xA9,a,0xA0,y,0x20,vector&255,vector>>8,
                      0x08,0x68,0x8D,0x00,0x06,0xA9,0x42,0x8D,0x01,0x06,
                      0x4C,0x11,0x04))
        m.bus.ram[0x400:0x400+len(code)] = code
        m.bus[0x601] = 0
        m.cpu.pc = 0x400
        m.run(budget)
        self.assertEqual(m.bus[0x601], 0x42, 'firmware call did not finish')
        return bool(m.bus[0x600] & 1)

    def print_text(self, m, text):
        m.bus.ram[0x500:0x500+len(text)] = text
        code = bytes((0xA2,0,0xBD,0,5,0x20,0,0xE1,0xE8,0xE0,len(text),
                      0xD0,0xF5,0x4C,0x0D,4))
        m.bus.ram[0x400:0x400+len(code)] = code
        m.cpu.pc = 0x400
        before = len(m.bus.serial.output)
        m.run(1500000)
        self.assertEqual(bytes(m.bus.serial.output[before:]), text)
        self.assertEqual(m.bus.serial.framing_errors, 0)

    def test_default_off_and_mode_validation(self):
        m = self.machine()
        self.assertEqual(m.bus.backpack.starts, 0)
        self.assertTrue(self.call(m, 0xE124, a=3))
        self.assertEqual(m.bus.backpack.starts, 0)
        self.assertEqual(m.bus[0x7FD8], 0)

    def test_mirror_scroll_crlf_wrap_edit_and_clear(self):
        m = self.machine()
        self.assertFalse(self.call(m, 0xE124, a=1))
        self.print_text(m, b'LINE 1\r\nLINE 2\r\nLINE 3\r\nLINE 4\r\nLINE 5')
        self.assertEqual(m.bus.backpack.lcd.lines, tuple(s.ljust(20) for s in
                         ('LINE 2','LINE 3','LINE 4','LINE 5')))
        self.assertFalse(self.call(m, 0xE127))
        self.print_text(m, b'ABCDEFGHIJKLMNOPQRSTU\bZ')
        self.assertEqual(m.bus.backpack.lcd.lines[:2], ('ABCDEFGHIJKLMNOPQRST', 'Z'.ljust(20)))
        self.assertEqual(m.bus.backpack.lcd.timing_errors, 0)
        self.assertGreater(m.bus.backpack.acks, 0)

    def test_dashboard_independent_status_and_serial(self):
        m = self.machine()
        self.assertFalse(self.call(m, 0xE124, a=2))
        rows = m.bus.backpack.lcd.lines
        self.assertEqual(rows[0], 'AMC-6502 STATUS'.ljust(20))
        self.assertIn('BANK 1: RESERVED', rows[1])
        self.assertIn('CPU 1MHz', rows[2])
        self.print_text(m, b'SERIAL LOG ONLY\r\n')
        self.assertEqual(m.bus.backpack.lcd.lines, rows)
        m.bus.ram[0x700:0x70A] = b'PUMP: RUN\0'
        self.assertFalse(self.call(m, 0xE12A, a=0, y=7))
        self.assertEqual(m.bus.backpack.lcd.lines[3], 'PUMP: RUN'.ljust(20))
        m.bus.ram[0x700:0x719] = b'X'*24+b'\0'
        self.assertFalse(self.call(m, 0xE12A, a=0, y=7))
        self.assertEqual(m.bus.backpack.lcd.lines[3], 'X'*20)

    def test_missing_or_wrong_address_is_bounded_and_serial_survives(self):
        for kwargs in ({'lcd_present':False}, {'lcd_address':0x3F}):
            m = self.machine(**kwargs)
            self.assertTrue(self.call(m, 0xE124, a=2))
            self.assertEqual(m.bus[0x7FD8], 0)
            self.assertEqual(m.bus[0x02FD], 0)
            self.print_text(m, b'NO LCD\r\n')
            self.assertEqual(m.bus.backpack.bytes_written, 0)

    def test_port_ownership_and_external_display_reset(self):
        m = self.machine()
        m.bus[0x02FC] = 0xA1
        m.bus[0xB00F] = 0xA1
        m.bus[0xB003] = 0xF1
        self.assertFalse(self.call(m, 0xE124, a=2))
        self.assertEqual(m.bus.ddra & 0xF3, 0xF1)
        self.assertEqual(m.bus.vias[0].ora & 0xF3, 0xA1)
        self.assertEqual(m.bus.ddra & 0x0C, 0)
        before = m.bus.backpack.lcd.lines
        m.reset()
        self.assertEqual(m.bus.backpack.lcd.lines, before)  # no LCD reset pin

    def test_host_inspection_has_no_side_effects(self):
        m = self.machine()
        self.call(m, 0xE124, a=2)
        before = deepcopy(m.bus.backpack.__dict__)
        lcd_before = deepcopy(m.bus.backpack.lcd.__dict__)
        cycles = m.cpu.processorCycles
        output=[]
        Terminal(m, output.append).handle(':lcd')
        self.assertIn('|AMC-6502 STATUS     |', output)
        self.assertEqual(m.bus.backpack.lcd.__dict__, lcd_before)
        self.assertEqual(m.cpu.processorCycles, cycles)
        self.assertEqual(m.bus.backpack.starts, before['starts'])

    def test_dashboard_mode_survives_bank_reset_and_updates_identity(self):
        m = self.machine()
        self.assertFalse(self.call(m, 0xE124, a=2))
        m.select_bank(2)
        m.run(500000)
        self.assertEqual(m.bus[0x7FD8], 2)
        self.assertIn('BANK 2: WOZ MONITOR', m.bus.backpack.lcd.lines[1])
        self.assertEqual(m.bus.backpack.lcd.timing_errors, 0)

    def test_mode_request_serviced_by_firmware_input_loop(self):
        m = Machine(ROM.read_bytes(), bank=3)
        m.run(1000000)
        Terminal(m, lambda _: None).handle(':lcd dashboard')
        m.run(500000)
        self.assertEqual(m.bus[0x7FD8], 2)
        self.assertIn('BANK 3:', m.bus.backpack.lcd.lines[1])
        m.bus.serial.feed(b'R')
        m.run(1500000)
        self.assertEqual(m.bus.backpack.lcd.lines[3], 'ALL CHECKS PASS'.ljust(20))
        self.assertFalse(self.call(m, 0xE124, a=0))
        self.assertEqual(m.bus.backpack.lcd.lines, (' '*20,)*4)
        self.assertFalse(m.bus.backpack.lcd.backlight)

    def test_basic_memory_probe_stops_before_lcd_workspace(self):
        m = Machine(ROM.read_bytes())
        m.run(150000)
        # Use actual BASIC prompt handling and its own auto-detection code.
        m.bus.ram[0x7F80:0x7F90] = b'K'*16
        m.bus.serial.feed(b'\r')
        m.run(750000)
        m.bus.serial.feed(b'\r')
        m.run(750000)
        self.assertIn(b'OK', m.bus.serial.output)
        self.assertEqual(m.bus[0x85] | m.bus[0x86] << 8, 0x7F80)
        self.assertEqual(m.bus.ram[0x7F80:0x7F90], b'K'*16)

    def test_echo_paced_loader_works_with_mirroring_enabled(self):
        from scripts.send_hex import EmulatorTransport, record, send, validate
        t = EmulatorTransport(ROM.read_bytes())
        ready_offset = t.offset
        t.expect(b'HEX READY\r\n')  # do not reconfigure during an incoming character
        t.machine.bus[0x02FD] = 1
        t.machine.run(250000)
        t.offset = ready_offset
        send(t, validate([record(0x700, b'LCD'), record(0, kind=1)]))
        self.assertEqual(t.machine.bus.ram[0x700:0x703], b'LCD')
        self.assertEqual(t.machine.bus.serial.framing_errors, 0)
