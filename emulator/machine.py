"""Classic CPU, banked ROM, and classic VIA timer/IRQ models."""
from py65.devices.mpu6502 import MPU
from emulator.serial import SerialPeer
from emulator.via import VIA6522
from emulator.lcd import I2CBackpack
from emulator.memory_map import VIA1_BASE, VIA2_BASE, SLOT_SIZE


class MemoryBus:
    def __init__(self, rom: bytes, bank=0, *, lcd_present=True, lcd_address=0x27):
        # Keep legacy 8 KB diagnostics as explicit single-bank fixtures.
        if len(rom) not in (0x2000, 0x10000):
            raise ValueError('Expected 8192-byte legacy fixture or 65536-byte bank image')
        self.rom = bytes(rom)
        self.legacy = len(rom) == 0x2000
        self.ram = bytearray(0x8000)
        if bank not in range(4) or (self.legacy and bank):
            raise ValueError("Invalid initial bank switch setting")
        self.bank = bank
        self.serial = SerialPeer()
        self.vias = [VIA6522(), VIA6522()]
        self.backpack = I2CBackpack(lcd_address, lcd_present)

    def __getitem__(self, address):
        if not 0 <= address <= 0xFFFF:
            raise IndexError(address)
        if address < 0x8000:
            return self.ram[address]
        if not self.legacy:
            if VIA1_BASE <= address < VIA2_BASE + SLOT_SIZE:
                index = (address - VIA1_BASE) // SLOT_SIZE
                self._input_pins()
                return self.vias[index].read(address & 15)
            if address >= 0xC000:
                return self.rom[self.bank * 0x4000 + address - 0xC000]
        elif address >= 0xE000:
            return self.rom[address - 0xE000]
        return 0xFF

    def peek(self, address):
        """Debugger read: no device acknowledgement, pin mutation, or time advance."""
        if not 0 <= address <= 0xFFFF:
            raise IndexError(address)
        if not self.legacy and VIA1_BASE <= address < VIA2_BASE + SLOT_SIZE:
            index = (address - VIA1_BASE) // SLOT_SIZE
            via = self.vias[index]
            inputs = self._input_value(self.serial.peek_rx()) if index == 0 else None
            return via.read(address & 15, side_effects=False, input_a=inputs)
        return self[address]

    def __setitem__(self, address, value):
        if not 0 <= address <= 0xFFFF:
            raise IndexError(address)
        value &= 0xFF
        if address < 0x8000:
            self.ram[address] = value
        elif not self.legacy and VIA1_BASE <= address < VIA2_BASE + SLOT_SIZE:
            self.vias[(address - VIA1_BASE) // SLOT_SIZE].write(address & 15, value)
            self.serial.drive_tx(self.vias[0].pins_a & 1)
            self._i2c_pins()

    def _input_value(self, rx):
        value = (self.vias[0].input_a & 0xF1) | (rx << 1) | 0x0C
        return value & 0xFB if self.backpack.pull_low else value

    def _input_pins(self):
        # SDA is pulled high when released, or low by the backpack ACK.
        self.vias[0].set_port_a(self._input_value(self.serial.rx) | 4)
        if self.backpack.pull_low:
            self.vias[0].input_a &= 0xFB

    def _i2c_pins(self):
        via = self.vias[0]
        sda = int(not (via.ddra & 4 and not via.ora & 4))
        scl = int(not (via.ddra & 8 and not via.ora & 8))
        self.backpack.drive(sda, scl, self.serial.time)
        self._input_pins()

    @property
    def ddra(self):
        return self.vias[0].ddra

    @property
    def irq(self):
        return not self.legacy and any(via.irq for via in self.vias)

    def tick(self, cycles, now):
        if not self.legacy:
            for via in self.vias:
                via.tick(cycles)
        self.serial.tick(now)

    def reset_devices(self):
        # LCD power is independent of CPU reset; rebase its remaining busy time
        # when the CPU/serial cycle epoch restarts at zero.
        self.backpack.lcd.busy_until = max(0, self.backpack.lcd.busy_until - self.serial.time)
        self.serial = SerialPeer()
        self.backpack.reset_bus()
        for via in self.vias:
            via.reset()


class Machine:
    def __init__(self, rom: bytes, bank=0, *, lcd_present=True, lcd_address=0x27):
        self.bus = MemoryBus(rom, bank=bank, lcd_present=lcd_present, lcd_address=lcd_address)
        self.cpu = MPU(memory=self.bus, pc=None)
        self.reset_generation = 0
        self.reset()

    def reset(self):
        """Reset CPU/devices and cycle epoch; retain RAM and bank toggle positions."""
        self.bus.reset_devices()
        self.cpu.reset()
        self.cpu.p |= self.cpu.INTERRUPT
        self.reset_generation += 1

    def select_bank(self, bank):
        """Host convenience: hold reset, set external toggles, release reset."""
        if self.bus.legacy:
            raise ValueError('Bank switching requires a four-bank image')
        if bank not in range(4):
            raise ValueError('Bank must be 0 through 3')
        self.set_bank_switches(bank)
        self.reset()

    def set_bank_switches(self, bank):
        """External switch positions; changes ROM immediately without issuing reset."""
        if self.bus.legacy or bank not in range(4):
            raise ValueError('Bank switches require a four-bank image and bank 0 through 3')
        self.bus.bank = bank

    def prepare_instruction(self):
        """Accept a pending IRQ before fetching an opcode; advance its entry cycles."""
        if self.bus.irq and not self.cpu.p & self.cpu.INTERRUPT:
            before = self.cpu.processorCycles
            self.cpu.irq()
            self.bus.tick(self.cpu.processorCycles - before, self.cpu.processorCycles)

    def step(self, *, prepare=True):
        """Execute one opcode, including any preceding IRQ entry and device cycles."""
        if prepare:
            self.prepare_instruction()
        before = self.cpu.processorCycles
        self.cpu.step()
        self.bus.tick(self.cpu.processorCycles - before, self.cpu.processorCycles)

    def run(self, instructions):
        if instructions < 0:
            raise ValueError('Instruction budget cannot be negative')
        for _ in range(instructions):
            self.step()
