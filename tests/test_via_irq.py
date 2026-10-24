from pathlib import Path
import unittest
from emulator.machine import Machine

ROOT = Path(__file__).resolve().parents[1]


class ViaIrqTests(unittest.TestCase):
    def machine(self):
        return Machine((ROOT / 'build/via-irq.bin').read_bytes() * 4)

    def test_firmware_receives_and_acknowledges_both_via_irqs(self):
        m = self.machine()
        m.run(1000)
        self.assertEqual(m.bus[0x0202], 0xC0)  # pending even while SEI masks CPU
        self.assertEqual(m.bus[0x0200], 1)
        self.assertEqual(m.bus[0x0201], 1)
        self.assertEqual(m.bus[0x0203], 0x42)
        self.assertFalse(m.bus.irq)
        self.assertEqual(m.cpu.sp, 0xFF)  # RTI and PHA/PLA restored stack
        for via in m.bus.vias:
            self.assertEqual(via.read(13), 0)

    def test_irq_entry_cycles_advance_both_devices(self):
        m = self.machine()
        # Place CPU on IRQ handler, which starts with a three-cycle PHA.
        m.cpu.p &= ~m.cpu.INTERRUPT
        m.cpu.p |= m.cpu.DECIMAL
        m.bus.vias[0].set_control('ca1', 0)
        m.bus.vias[0].write(14, 0x82)
        m.bus.vias[1].write(8, 100)
        m.bus.vias[1].write(9, 0)
        m.run(1)
        self.assertEqual(m.cpu.processorCycles, 10)  # 7 IRQ entry + 3 PHA
        self.assertEqual(m.bus.vias[1].t2_counter, 91)
        self.assertTrue(m.cpu.p & m.cpu.INTERRUPT)
        self.assertTrue(m.cpu.p & m.cpu.DECIMAL)  # NMOS IRQ does not clear decimal mode

    def test_unacknowledged_level_irq_reenters_after_rti(self):
        m = self.machine()
        m.cpu.p &= ~m.cpu.INTERRUPT
        m.bus.vias[0].set_control('ca1', 0)
        m.bus.vias[0].write(14, 0x82)
        # Handler only acknowledges timer flags, so CA1 holds IRQ active.
        m.run(9)  # full handler through RTI
        self.assertFalse(m.cpu.p & m.cpu.INTERRUPT)
        before = m.cpu.processorCycles
        m.run(1)
        self.assertEqual(m.cpu.processorCycles - before, 10)
        m.bus[0xB001]  # acknowledge CA1
        self.assertFalse(m.bus.irq)

    def test_bank_reset_removes_irq_and_restarts_both_devices(self):
        m = self.machine()
        for via in m.bus.vias:
            via.write(14, 0xC0)
            via.write(4, 0)
            via.write(5, 0)
        m.bus.tick(2, 2)
        self.assertTrue(m.bus.irq)
        m.bus[0x7000] = 0xAB
        m.select_bank((m.bus.bank + 1) % 4)
        self.assertEqual(m.bus.bank, 1)
        self.assertEqual(m.bus[0x7000], 0xAB)
        self.assertEqual(m.cpu.processorCycles, 0)
        self.assertFalse(m.bus.irq)
        self.assertTrue(m.cpu.p & m.cpu.INTERRUPT)
        self.assertTrue(all(v.read(14) == 0x80 for v in m.bus.vias))

    def test_shared_irq_stays_asserted_until_both_sources_acknowledged(self):
        m = self.machine()
        for via in m.bus.vias:
            via.write(14, 0xC0)
            via.write(4, 0)
            via.write(5, 0)
        m.bus.tick(2, 2)
        self.assertTrue(m.bus.irq)
        m.bus[0xB004]
        self.assertTrue(m.bus.irq)
        m.bus[0xB804]
        self.assertFalse(m.bus.irq)

    def test_free_running_timer_repeatedly_interrupts_real_firmware(self):
        m = self.machine()
        for offset, value in enumerate((0xEA, 0x4C, 0x00, 0x04)):  # NOP; JMP $0400
            m.bus[0x0400 + offset] = value
        m.cpu.pc = 0x0400
        m.cpu.p &= ~m.cpu.INTERRUPT
        via = m.bus.vias[0]
        via.write(11, 0x40)
        via.write(14, 0xC0)
        via.write(4, 100)
        via.write(5, 0)
        m.run(500)
        self.assertGreater(m.bus[0x0200], 3)
        self.assertEqual(m.bus[0x0201], 0)
