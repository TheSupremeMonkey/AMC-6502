from pathlib import Path
import unittest

from emulator.machine import Machine, MemoryBus

ROM = Path(__file__).resolve().parents[1] / "build/diagnostic.bin"


class MachineTests(unittest.TestCase):
    def test_diagnostic_boot_and_reset(self):
        machine = Machine(ROM.read_bytes())
        self.assertEqual(machine.cpu.pc, 0xE000)
        self.assertTrue(machine.cpu.p & machine.cpu.INTERRUPT)
        machine.run(100)
        self.assertEqual(machine.bus[0x0200], 0x42)
        self.assertEqual(machine.bus[0], 0x55)
        self.assertEqual(machine.bus[0x7FFF], 0x55)
        self.assertEqual(machine.bus[0x0100], 0xAA)
        self.assertEqual(machine.bus[0xE000], 0x78)
        machine.bus[0x1234] = 0xAB
        machine.reset()
        self.assertEqual(machine.cpu.pc, 0xE000)
        self.assertTrue(machine.cpu.p & machine.cpu.INTERRUPT)
        self.assertEqual(machine.bus[0x1234], 0xAB)
        machine.run(6)
        self.assertEqual(machine.bus[0x0200], 0)
        machine.run(100)
        self.assertEqual(machine.bus[0x0200], 0x42)

    def test_memory_boundaries_and_unimplemented_io(self):
        bus = MemoryBus(ROM.read_bytes())
        for address in (0, 0x7FFF):
            bus[address] = 0xA5
            self.assertEqual(bus[address], 0xA5)
        for address in (0x8000, 0x800F, 0x8010, 0x801F, 0x8020, 0xDFFF):
            bus[address] = 0
            self.assertEqual(bus[address], 0xFF)
        for address in (0xE000, 0xFFFF):
            before = bus[address]
            bus[address] = before ^ 0xFF
            self.assertEqual(bus[address], before)

    def test_rom_size_and_execution_budget(self):
        with self.assertRaises(ValueError):
            MemoryBus(b"")
        machine = Machine(ROM.read_bytes())
        before = (machine.cpu.pc, machine.cpu.processorCycles)
        machine.run(0)
        self.assertEqual((machine.cpu.pc, machine.cpu.processorCycles), before)
        with self.assertRaises(ValueError):
            machine.run(-1)
        machine.run(1)
        self.assertEqual(machine.cpu.pc, 0xE001)
        self.assertEqual(machine.cpu.processorCycles, 2)
