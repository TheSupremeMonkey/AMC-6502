"""Debugger behavior at machine boundaries; device inspection must be inert."""
from copy import deepcopy
import unittest

from emulator.debugger import Debugger
from emulator.machine import Machine
from emulator.terminal import Terminal


def test_machine():
    bank = bytearray([0xFF] * 0x4000)
    bank[0x3FFA:] = bytes((0, 5, 0, 4, 0, 5))  # NMI=$0500 RESET=$0400 IRQ=$0500
    m = Machine(bytes(bank) * 4)
    m.bus.ram[0x400:0x409] = bytes((0xA9, 0x42, 0x8D, 0, 3, 0xE8, 0x4C, 5, 4))
    return m


class DebuggerTests(unittest.TestCase):
    def test_step_runs_one_instruction_and_keeps_device_time(self):
        m = test_machine()
        d = Debugger(m)
        d.breakpoints.add((0, 0x400))
        d.step()
        self.assertEqual((m.cpu.pc, m.cpu.a, m.cpu.processorCycles), (0x402, 0x42, 2))
        d.step()
        self.assertEqual(m.bus[0x300], 0x42)
        self.assertEqual(m.bus.serial.time, m.cpu.processorCycles)
        self.assertFalse(d.running)

    def test_breakpoint_stops_before_write_and_resume_executes_once(self):
        m = test_machine()
        terminal = Terminal(m, lambda _: None)
        d = terminal.debugger
        d.breakpoints.add((0, 0x402))
        d.resume()
        self.assertEqual(d.run_chunk(20), 1)
        self.assertEqual(d.reason, 'breakpoint')
        self.assertEqual(m.bus[0x300], 0)
        terminal.handle(':regs')  # inspecting must not prevent resume past a hit
        d.resume(1)
        self.assertEqual(d.run_chunk(20), 1)
        self.assertEqual(m.bus[0x300], 0x42)
        self.assertEqual(m.cpu.pc, 0x405)

    def test_loop_breakpoint_hits_again_after_resume(self):
        m = test_machine()
        d = Debugger(m)
        d.breakpoints.add((0, 0x405))
        d.resume()
        d.run_chunk()
        self.assertEqual(m.cpu.x, 0)
        d.resume()
        self.assertEqual(d.run_chunk(), 2)
        self.assertEqual(m.cpu.x, 1)
        self.assertEqual(m.cpu.pc, 0x405)
        self.assertEqual(d.reason, 'breakpoint')

    def test_bank_scoped_and_global_breakpoints(self):
        m = test_machine()
        d = Debugger(m)
        d.breakpoints.add((1, 0x400))
        d.resume(1)
        self.assertEqual(d.run_chunk(), 1)  # bank 0 does not match bank 1
        m.select_bank(1)
        d.resume()
        self.assertEqual(d.run_chunk(), 0)
        self.assertEqual(m.cpu.pc, 0x400)
        d.breakpoints = {(None, 0x400)}
        m.select_bank(2)
        d.resume()
        self.assertEqual(d.run_chunk(), 0)
        self.assertEqual(d.reason, 'breakpoint')

    def test_irq_handler_breakpoint_precedes_first_handler_opcode(self):
        m = test_machine()
        m.bus[0x500] = 0xE8  # INX
        m.cpu.p &= ~m.cpu.INTERRUPT
        via = m.bus.vias[0]
        via.set_control('ca1', 0)
        via.write(14, 0x82)
        d = Debugger(m)
        d.breakpoints.add((0, 0x500))
        d.resume()
        self.assertEqual(d.run_chunk(), 0)
        self.assertEqual((m.cpu.pc, m.cpu.x, m.cpu.processorCycles), (0x500, 0, 7))
        self.assertEqual(m.bus.serial.time, 7)
        d.step()
        self.assertEqual((m.cpu.pc, m.cpu.x, m.cpu.processorCycles), (0x501, 1, 9))

    def test_memory_inspection_does_not_acknowledge_irq_or_consume_serial(self):
        m = test_machine()
        via = m.bus.vias[0]
        via.write(4, 0)
        via.write(5, 0)
        via.tick(2)
        via.set_control('ca1', 0)
        via.set_control('ca2', 0)
        via.write(14, 0xFF)
        m.bus.serial.feed(b'A')
        m.bus.serial.time = 100000  # expired frame must not be popped by peek
        state = deepcopy(via.__dict__)
        frames = list(m.bus.serial.frames)
        d = Debugger(m)
        self.assertEqual(len(d.memory(0xB000, 32)), 32)
        self.assertEqual(via.__dict__, state)
        self.assertEqual(list(m.bus.serial.frames), frames)
        self.assertEqual(m.cpu.processorCycles, 0)
        self.assertTrue(via.irq)
        m.bus[0xB004]  # real CPU-style read acknowledges T1
        self.assertFalse(via.ifr & 0x40)

    def test_peek_shows_live_rx_pin_without_mutating_port(self):
        m = test_machine()
        m.bus.serial.feed(b'A')
        m.bus.serial.time = 1000  # start bit
        before = m.bus.vias[0].input_a
        self.assertEqual(m.bus.peek(0xB001) & 2, 0)
        self.assertEqual(m.bus.vias[0].input_a, before)
        self.assertEqual(len(m.bus.serial.frames), 1)

    def test_ram_edit_validation_and_rom_protection(self):
        m = test_machine()
        d = Debugger(m)
        d.write_memory(0x300, [0x41, 0x42])
        self.assertEqual(d.memory(0x300, 2), b'AB')
        for address, values in ((0x7FFF, [1, 2]), (0x8000, [1]), (0xC000, [1]), (0x300, [7, 256])):
            with self.assertRaises(ValueError):
                d.write_memory(address, values)
        self.assertEqual(d.memory(0x300, 2), b'AB')
        with self.assertRaises(ValueError):
            d.memory(0xFFFF, 2)

    def test_host_bank_reset_preserves_breakpoints(self):
        m = test_machine()
        d = Debugger(m)
        d.breakpoints.add((2, 0x400))
        m.select_bank(2)
        d.resume()
        self.assertEqual(d.run_chunk(), 0)
        self.assertEqual(m.bus.bank, 2)
        self.assertEqual(m.cpu.processorCycles, 0)
        self.assertEqual(d.reason, 'breakpoint')

    def test_commands_parse_hex_counts_errors_and_pause_for_inspection(self):
        m = test_machine()
        messages = []
        t = Terminal(m, messages.append)
        t.handle(':write $0300 41 42 43')
        t.handle(':run')
        t.handle(':mem 0x300 3')
        self.assertFalse(t.debugger.running)
        self.assertIn('41 42 43', messages[-1])
        self.assertIn('|ABC|', messages[-1])
        for command in (':write 0300 44 GG', ':step 0', ':bank 5', ':pc 10000', ':unknown'):
            t.handle(command)
            self.assertTrue(messages[-1].startswith('Error:'))
        self.assertEqual(m.bus.ram[0x300:0x303], b'ABC')
        t.handle(':break 0400')
        t.handle(':break E200 all')
        self.assertEqual(t.debugger.breakpoints, {(0, 0x400), (None, 0xE200)})
        t.handle(':delete 0400')
        t.handle(':delete all')
        self.assertFalse(t.debugger.breakpoints)

    def test_reset_does_not_skip_breakpoint_at_same_address(self):
        m = test_machine()
        d = Debugger(m)
        d.breakpoints.add((0, 0x400))
        d.resume()
        self.assertEqual(d.run_chunk(), 0)
        m.reset()
        d.resume()
        self.assertEqual(d.run_chunk(), 0)
        self.assertEqual(m.cpu.processorCycles, 0)
