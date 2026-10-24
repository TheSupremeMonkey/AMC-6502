"""Observable boundaries, non-overlapping VIA aliases and unpopulated slots."""
import unittest
from emulator.machine import MemoryBus
from emulator.memory_map import VIA1_BASE, VIA2_BASE, SLOT_SIZE


class AddressDecodeTests(unittest.TestCase):
    def bus(self):
        return MemoryBus(b''.join(bytes((0x60+b,))*0x4000 for b in range(4)))

    def test_every_cpu_address_matches_current_population(self):
        bus = self.bus()
        for index, via in enumerate(bus.vias):
            via.write(2, 255)
            via.write(0, 0x11*(index+1))
        for address in range(65536):
            if address < 0x8000:
                expected = 0
            elif address < VIA1_BASE:
                expected = 255
            elif address < 0xC000:
                index = (address-VIA1_BASE)//SLOT_SIZE
                expected = bus.vias[index].read(address&15, side_effects=False)
            else:
                expected = 0x60
            self.assertEqual(bus.peek(address), expected, f'${address:04X}')

    def test_device_boundary_writes_do_not_reach_neighbor(self):
        bus = self.bus()
        bus[VIA1_BASE+3] = 0x55
        bus[VIA2_BASE+3] = 0xAA
        bus[0xAFF3] = 0xFF  # unpopulated slot immediately below VIA1
        self.assertEqual(bus[VIA1_BASE+0x7F3], 0x55)
        self.assertEqual(bus[VIA2_BASE+0x7F3], 0xAA)
        bus[0xC003] = 0  # ROM immediately above VIA2
        self.assertEqual(bus[VIA2_BASE+3], 0xAA)
        self.assertEqual(bus[0xC003], 0x60)

    def test_aliased_timer_read_acknowledges_only_selected_via(self):
        bus = self.bus()
        for via in bus.vias:
            via.write(14, 0xC0)
            via.write(4, 0)
            via.write(5, 0)
            via.tick(2)
        self.assertTrue(bus.irq)
        bus[VIA1_BASE+0x7F4]
        self.assertFalse(bus.vias[0].irq)
        self.assertTrue(bus.vias[1].irq)
        bus[VIA2_BASE+0x7F4]
        self.assertFalse(bus.irq)
