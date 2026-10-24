"""Bank 3 diagnostics report both working hardware and injected faults."""
from pathlib import Path
import unittest

from emulator.machine import Machine
from emulator.via import VIA6522

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticsRomTests(unittest.TestCase):
    def machine(self):
        m = Machine((ROOT / 'build/amc6502.bin').read_bytes())
        for _ in range(3):
            m.select_bank((m.bus.bank + 1) % 4)
        return m

    def output(self, m):
        self.assertEqual(m.bus.serial.framing_errors, 0)
        return bytes(m.bus.serial.output).decode('ascii')

    def test_bank3_reports_pass_restores_ram_and_reruns(self):
        m = self.machine()
        original = bytes((i * 37 + 11) & 255 for i in range(0x7C80))
        m.bus.ram[0x300:0x7F80] = original
        m.run(1000000)
        output = self.output(m)
        self.assertIn('AMC-6502 DIAGNOSTICS - BANK 3', output)
        self.assertIn('PASS RAM $0300-$7F7F (restored)', output)
        self.assertEqual(output.count('PASS T1 + IRQ'), 2)
        self.assertEqual(output.count('PASS T2 + IRQ'), 2)
        self.assertIn('ALL CHECKS PASS', output)
        self.assertNotIn('FAIL', output)
        self.assertEqual(bytes(m.bus.ram[0x300:0x7F80]), original)
        self.assertFalse(m.bus.irq)
        self.assertTrue(m.cpu.p & m.cpu.INTERRUPT)
        m.bus.serial.feed(b'R')
        m.run(1000000)
        self.assertEqual(self.output(m).count('ALL CHECKS PASS'), 2)
        self.assertEqual(bytes(m.bus.ram[0x300:0x7F80]), original)
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 0)
        m.run(125000)
        self.assertIn('MEMORY SIZE?', self.output(m))
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 1)
        m.run(100)
        # Shared reset replaces the diagnostic IRQ vector with its default.
        pointer = m.bus[0x2F2] | m.bus[0x2F3] << 8
        self.assertGreaterEqual(pointer, 0xE000)

    def test_missing_via_timers_report_failure_without_hanging(self):
        class StoppedTimers(VIA6522):
            def tick(self, cycles):
                pass
        m = self.machine()
        m.bus.vias[1] = StoppedTimers()
        m.run(1000000)
        output = self.output(m)
        self.assertIn('VIA 1\r\nPASS T1 + IRQ\r\nPASS T2 + IRQ', output)
        self.assertIn('VIA 2\r\nFAIL T1 + IRQ\r\nFAIL T2 + IRQ', output)
        self.assertIn('DIAGNOSTIC FAILURE', output)
        self.assertNotIn('ALL CHECKS PASS', output)
        self.assertIn('R to rerun', output)

    def test_stuck_ram_byte_reports_failure(self):
        class StuckRam(bytearray):
            def __getitem__(self, index):
                if index == 0x333:
                    return 0
                return super().__getitem__(index)
        m = self.machine()
        m.bus.ram = StuckRam(m.bus.ram)
        m.run(250000)
        output = self.output(m)
        self.assertIn('FAIL RAM $0300-$7F7F', output)
        self.assertIn('DIAGNOSTIC FAILURE', output)
        self.assertNotIn('ALL CHECKS PASS', output)
        self.assertEqual(output.count('PASS T1 + IRQ'), 2)

    def test_suppressed_irq_reports_failure_without_hanging(self):
        class SuppressedIRQ(VIA6522):
            @property
            def irq(self):
                return False
        m = self.machine()
        m.bus.vias[1] = SuppressedIRQ()
        m.run(1000000)
        output = self.output(m)
        self.assertIn('VIA 2\r\nFAIL T1 + IRQ\r\nFAIL T2 + IRQ', output)
        self.assertIn('DIAGNOSTIC FAILURE', output)
        self.assertIn('R to rerun', output)
