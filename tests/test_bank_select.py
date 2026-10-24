"""Physical toggle selection, mirrored decode and retired software service."""
from pathlib import Path
import unittest
from emulator.machine import Machine

ROM = Path(__file__).resolve().parents[1] / 'build/amc6502.bin'


class BankSwitchTests(unittest.TestCase):
    def test_power_on_switch_positions_and_reset_retention(self):
        for bank in range(4):
            m = Machine(ROM.read_bytes(), bank=bank)
            m.bus[0x7000] = 0xA5
            m.bus.vias[0].write(3, 255)
            m.reset()
            self.assertEqual(m.bus.bank, bank)
            self.assertEqual(m.bus[0x7000], 0xA5)
            self.assertEqual(m.bus.ddra, 0)
            m.run(150000)
            self.assertIn(f'BANK {bank}:'.encode(), bytes(m.bus.serial.output))
            self.assertEqual(m.bus.serial.framing_errors, 0)

    def test_toggles_change_rom_without_reset(self):
        m = Machine(ROM.read_bytes())
        generation, pc = m.reset_generation, m.cpu.pc
        m.set_bank_switches(2)
        self.assertEqual(m.bus[0xC000], m.bus.rom[0x8000])
        self.assertEqual((m.reset_generation, m.cpu.pc), (generation, pc))
        m.reset()
        self.assertEqual(m.bus.bank, 2)

    def test_all_via_aliases_and_no_bank_register(self):
        m = Machine(ROM.read_bytes())
        for index, base in enumerate((0xB000, 0xB800)):
            for offset in range(0, 0x800, 16):
                m.bus[base+offset+3] = (offset//16) & 255
                self.assertEqual(m.bus[base+3], (offset//16) & 255)
                self.assertEqual(m.bus.peek(base+offset+3), m.bus[base+3])
            m.bus[base+2] = 255
            m.bus[base] = 0xA5
            self.assertEqual(m.bus[base+0x7F0], 0xA5)
        generation = m.reset_generation
        m.bus[0x8020] = 2
        self.assertEqual(m.bus.vias[0].orb, 0xA5)
        self.assertEqual(m.bus.bank, 0)
        self.assertEqual(m.reset_generation, generation)
        for address in (0x8000, 0x87FF, 0x8800, 0x8FFF, 0x9000, 0x97FF, 0x9800, 0x9FFF, 0xA000, 0xA7FF, 0xA800, 0xAFFF):
            m.bus[address] = 0
            self.assertEqual(m.bus[address], 255)

    def test_retired_vector_returns_failure_for_every_bank(self):
        for bank in range(4):
            m = Machine(ROM.read_bytes())
            m.bus.ram[0x400:0x40D] = bytes((0xA9, bank, 0x20, 0x06, 0xE1,
                                           0x08, 0x68, 0x8D, 0, 2, 0x4C, 0x0A, 4))
            m.cpu.pc = 0x400
            generation = m.reset_generation
            m.run(30)
            self.assertTrue(m.bus[0x200] & 1)
            self.assertEqual(m.reset_generation, generation)
            self.assertEqual(m.bus.bank, 0)

    def test_diagnostic_numbers_do_not_switch(self):
        m = Machine(ROM.read_bytes(), bank=3)
        m.run(1000000)
        self.assertIn(b'ALL CHECKS PASS', m.bus.serial.output)
        generation = m.reset_generation
        m.bus.serial.feed(b'1234\r')
        m.run(50000)
        self.assertEqual((m.bus.bank, m.reset_generation), (3, generation))

    def test_serial_preserves_reserved_port_bits(self):
        m = Machine(ROM.read_bytes())
        m.run(150000)
        m.bus[0x02FC] = 0xA9
        m.bus[0xB00F] = 0xA9
        m.bus[0xB003] = 0xF1
        # Real COUT calls for alternating data; other port bits must survive.
        code = bytes((0xA9, 0x55, 0x20, 0, 0xE1, 0xA9, 0x2A, 0x20, 0, 0xE1,
                      0x4C, 0x0A, 4))
        m.bus.ram[0x400:0x400+len(code)] = code
        m.cpu.pc = 0x400
        before = len(m.bus.serial.output)
        m.run(3000)
        self.assertEqual(m.bus.vias[0].ora, 0xA9)
        self.assertEqual(m.bus.ddra, 0xF1)
        self.assertEqual(bytes(m.bus.serial.output[before:]), b'U*')
        self.assertEqual(m.bus.serial.framing_errors, 0)
