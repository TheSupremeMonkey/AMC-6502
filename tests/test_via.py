import unittest
from emulator.via import VIA6522


class ViaTests(unittest.TestCase):
    def setUp(self):
        self.via = VIA6522()

    def load_t1(self, value):
        self.via.write(4, value & 255)
        self.via.write(5, value >> 8)

    def load_t2(self, value):
        self.via.write(8, value & 255)
        self.via.write(9, value >> 8)

    def test_t1_exact_expiry_and_masked_pending_interrupt(self):
        v = self.via
        self.load_t1(3)
        v.tick(4)
        self.assertEqual(v.read(13), 0)
        v.tick(1)
        self.assertEqual(v.read(13), 0x40)
        self.assertFalse(v.irq)
        v.write(14, 0xC0)
        self.assertEqual(v.read(13), 0xC0)
        self.assertTrue(v.irq)
        v.read(5)
        self.assertTrue(v.irq)
        v.read(4)
        self.assertFalse(v.irq)
        v.tick(2 * 65536)
        self.assertEqual(v.read(13), 0)
        self.load_t1(0)
        v.tick(1)
        self.assertFalse(v.irq)
        v.tick(1)
        self.assertTrue(v.irq)

    def test_t1_free_run_reload_and_pb7(self):
        v = self.via
        v.write(2, 0x80)
        v.write(11, 0xC0)
        v.write(14, 0xC0)
        self.load_t1(2)
        self.assertEqual(v.pins_b & 0x80, 0)
        v.tick(4)
        self.assertEqual(v.pins_b & 0x80, 0x80)
        self.assertTrue(v.irq)
        v.read(4)
        v.tick(3)
        self.assertFalse(v.irq)
        v.tick(1)
        self.assertTrue(v.irq)
        self.assertEqual(v.pins_b & 0x80, 0)
        # Updating the latch does not restart the current countdown.
        v.write(6, 5)
        v.write(7, 0)
        self.assertFalse(v.irq)
        v.tick(4)
        self.assertTrue(v.irq)
        v.read(4)
        v.tick(6)
        self.assertFalse(v.irq)
        v.tick(1)
        self.assertTrue(v.irq)

    def test_timer_advance_is_independent_of_chunk_size(self):
        v = self.via
        v.write(11, 0x40)
        self.load_t1(7)
        self.load_t2(11)
        other = VIA6522()
        other.write(11, 0x40)
        for r, value in ((4, 7), (5, 0), (8, 11), (9, 0)):
            other.write(r, value)
        v.tick(10003)
        for _ in range(10003):
            other.tick(1)
        self.assertEqual((v.t1_counter, v.t2_counter, v.pb7, v.read(13)),
                         (other.t1_counter, other.t2_counter, other.pb7, other.read(13)))

    def test_t2_one_shot_and_acknowledgement(self):
        v = self.via
        v.write(14, 0xA0)
        self.load_t2(1)
        v.tick(2)
        self.assertFalse(v.irq)
        v.tick(1)
        self.assertEqual(v.read(13), 0xA0)
        v.read(9)
        self.assertTrue(v.irq)
        v.read(8)
        self.assertFalse(v.irq)
        v.tick(65536)
        self.assertFalse(v.irq)
        self.load_t2(0)
        v.tick(2)
        self.assertTrue(v.irq)

    def test_t2_counts_pb6_falling_edges(self):
        v = self.via
        v.write(11, 0x20)
        self.load_t2(1)
        v.tick(100000)
        self.assertEqual(v.t2_counter, 1)
        v.set_port_b(0xBF)
        self.assertEqual(v.t2_counter, 0)
        v.set_port_b(0xBF)
        self.assertEqual(v.read(13), 0)
        v.set_port_b(0xFF)
        v.set_port_b(0xBF)
        self.assertEqual(v.read(13), 0x20)
        v.read(8)
        for _ in range(3):
            v.set_port_b(0xFF)
            v.set_port_b(0xBF)
        self.assertEqual(v.read(13), 0)

    def test_ier_bit_commands_and_selective_ifr_clear(self):
        v = self.via
        self.load_t1(0)
        self.load_t2(0)
        v.tick(2)
        self.assertEqual(v.read(13), 0x60)
        self.assertEqual(v.read(14), 0x80)
        v.write(14, 0xC0)
        v.write(14, 0xA0)
        self.assertEqual(v.read(14), 0xE0)
        v.write(13, 0x80)  # summary bit is not a clear-all command
        self.assertEqual(v.read(13), 0xE0)
        v.write(13, 0x40)
        self.assertEqual(v.read(13), 0xA0)
        v.write(14, 0x20)
        self.assertEqual(v.read(13), 0x20)
        v.write(14, 0xA0)
        self.assertTrue(v.irq)
        v.write(13, 0x20)
        self.assertFalse(v.irq)

    def test_ports_latches_and_no_handshake_alias(self):
        v = self.via
        v.write(3, 0xF0)
        v.write(15, 0xA0)
        v.set_port_a(0x05)
        self.assertEqual(v.read(15), 0xA5)
        v.write(11, 1)
        v.set_control('ca1', 0)
        v.set_port_a(0x0F)
        self.assertEqual(v.read(15), 0xA5)
        self.assertEqual(v.read(13), 2)
        self.assertEqual(v.read(1), 0xA5)
        self.assertEqual(v.read(13), 0)
        v.write(2, 0x0F)
        v.write(0, 0x03)
        v.set_port_b(0xA0)
        self.assertEqual(v.read(0), 0xA3)

    def test_control_edge_polarity_and_independent_ca2(self):
        v = self.via
        v.write(12, 0x03)  # CA1 rising, CA2 falling independent
        v.set_control('ca1', 0)
        self.assertEqual(v.read(13), 0)
        v.set_control('ca1', 1)
        v.set_control('ca2', 0)
        self.assertEqual(v.read(13), 3)
        v.read(1)
        self.assertEqual(v.read(13), 1)
        v.write(13, 1)
        v.set_control('cb1', 0)
        v.set_control('cb2', 0)
        self.assertEqual(v.read(13), 0x18)
        v.read(0)
        self.assertEqual(v.read(13), 0)

    def test_reset_clears_pending_interrupts_and_timers(self):
        v = self.via
        v.write(14, 0xFF)
        self.load_t1(0)
        v.tick(2)
        self.assertTrue(v.irq)
        v.reset()
        v.tick(100000)
        self.assertFalse(v.irq)
        self.assertEqual(v.read(13), 0)
        self.assertEqual(v.read(14), 0x80)
        self.assertEqual(v.read(3), 0)
        self.assertEqual(v.read(2), 0)

    def test_unimplemented_modes_fail_explicitly(self):
        v = self.via
        with self.assertRaises(NotImplementedError):
            v.write(11, 0x04)
        with self.assertRaises(NotImplementedError):
            v.write(12, 0x08)
        self.assertEqual(v.read(11), 0)
        self.assertEqual(v.read(12), 0)
        v.write(12, 0xEC)  # CA2 fixed low, CB2 fixed high
        self.assertEqual(v.lines['ca2'], 0)
        self.assertEqual(v.lines['cb2'], 1)
        v.set_control('ca2', 1)
        self.assertEqual(v.lines['ca2'], 0)

    def test_timer1_one_shot_pb7_and_latch_writes_do_not_start(self):
        v = self.via
        v.write(2, 0x80)
        v.write(11, 0x80)
        v.write(6, 3)
        v.write(7, 0)
        v.tick(100)
        self.assertEqual(v.read(13), 0)
        self.assertFalse(v.t1_running)
        v.write(5, 0)
        self.assertEqual(v.pins_b & 0x80, 0)
        v.tick(5)
        self.assertEqual(v.pins_b & 0x80, 0x80)
        v.read(4)
        v.tick(65536)
        self.assertEqual(v.pins_b & 0x80, 0x80)
        self.assertEqual(v.read(13), 0)
