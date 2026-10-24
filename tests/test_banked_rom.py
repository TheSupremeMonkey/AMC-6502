"""Real BASIC/Woz firmware through VIA pins, serial framing and bank reset."""
from pathlib import Path
import unittest
from emulator.machine import Machine

ROOT = Path(__file__).resolve().parents[1]


class BankedRomTests(unittest.TestCase):
    def setUp(self):
        self.image = (ROOT / 'build/amc6502.bin').read_bytes()
        self.machine = Machine(self.image)

    def output(self):
        return bytes(self.machine.bus.serial.output).decode('ascii')

    def command(self, text, budget=750000):
        self.machine.bus.serial.feed(text.encode('ascii') + b'\r')
        self.machine.run(budget)
        self.assertEqual(self.machine.bus.serial.framing_errors, 0)
        return self.output()

    def test_image_layout_and_mirrored_kernel(self):
        self.assertEqual(len(self.image), 65536)
        kernel = self.image[0x2000:0x4000]
        descriptions = ('BANK 0: MICROSOFT BASIC', 'BANK 1: RESERVED',
                        'BANK 2: WOZ MONITOR', 'BANK 3: HARDWARE DIAGNOSTICS')
        for bank, description in enumerate(descriptions):
            upper = self.image[bank*0x4000+0x2000:(bank+1)*0x4000]
            self.assertEqual(upper[:0x1FC0], kernel[:0x1FC0])
            self.assertEqual(upper[0x1FE0:], kernel[0x1FE0:])
            record = upper[0x1FC0:0x1FE0]
            self.assertEqual(record, description.encode('ascii').ljust(32, b'\0'))
        self.assertNotEqual(self.image[:0x2000], self.image[0x8000:0xA000])
        self.assertEqual(self.machine.cpu.pc, self.machine.bus[0xFFFC] | self.machine.bus[0xFFFD] << 8)
        for address in (0xC000, 0xDFFF, 0xE000, 0xFFFF):
            before = self.machine.bus[address]
            self.machine.bus[address] = before ^ 0xFF
            self.assertEqual(self.machine.bus[address], before)

    def test_basic_program_and_woz_switch_round_trip(self):
        m = self.machine
        m.run(125000)
        self.assertIn('MEMORY SIZE?', self.output())
        self.assertIn('TERMINAL WIDTH?', self.command(''))
        self.assertIn('OK', self.command(''))
        self.assertIn('\r\n 4 \r\n', self.command('PRINT 2+2'))
        self.assertIn('?SN ERROR', self.command('LOAD'))
        self.command('10 PRINT "AMC BASIC"')
        self.command('20 END')
        before = len(self.output())
        self.assertIn('AMC BASIC', self.command('RUN')[before:])
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 1)
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 2)
        self.assertEqual(m.cpu.processorCycles, 0)
        self.assertEqual(m.bus.ddra, 0)
        m.run(125000)
        self.assertTrue(self.output().endswith('\\\r'))
        self.command('0300: AB')
        self.assertEqual(m.bus[0x0300], 0xAB)
        before = len(self.output())
        self.assertIn('0300: AB', self.command('0300')[before:])
        m.bus[0x7000] = 0x5A
        m.reset()
        self.assertEqual(m.bus.bank, 2)
        self.assertEqual(m.bus[0x7000], 0x5A)
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 3)
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 0)
        self.assertEqual(m.bus[0x7000], 0x5A)
        m.run(125000)
        self.assertIn('MEMORY SIZE?', self.output())
        self.assertNotIn('AMC BASIC', self.output())

    def test_via_direction_and_reset(self):
        bus = self.machine.bus
        self.assertEqual(bus[0xB003], 0)
        bus[0xB001] = 0
        self.assertEqual(bus[0xB001] & 1, 1)  # undriven input pulled high
        bus[0xB003] = 1
        self.assertEqual(bus[0xB001] & 1, 0)
        bus.serial.feed(b'A')
        self.machine.select_bank((self.machine.bus.bank + 1) % 4)
        self.assertEqual(bus[0xB003], 0)
        self.assertEqual(len(bus.serial.frames), 0)

    def test_shared_boot_banner_on_every_bank_reset(self):
        m = self.machine
        descriptions = ('BANK 0: MICROSOFT BASIC', 'BANK 1: RESERVED',
                        'BANK 2: WOZ MONITOR', 'BANK 3: HARDWARE DIAGNOSTICS')
        for bank, description in enumerate(descriptions):
            self.assertEqual(m.bus.bank, bank)
            m.run(125000)
            output = self.output()
            self.assertTrue(output.startswith('\r\n   /\\'))
            self.assertEqual(output.count('A M C - 6 5 0 2'), 1)
            self.assertIn('ASTROMONKEY MICRO COMPUTER', output)
            self.assertIn('READY FOR LAUNCH', output)
            self.assertIn(description + '\r\n', output)
            self.assertEqual(output.count(description + '\r\n'), 1)
            self.assertEqual(m.bus.serial.framing_errors, 0)
            m.select_bank((m.bus.bank + 1) % 4)
        m.run(125000)
        self.assertEqual(self.output().count('READY FOR LAUNCH'), 1)
        self.assertIn('MEMORY SIZE?', self.output())
