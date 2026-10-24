"""PCF8574 write-side I2C and HD44780 20x4 character-display subset.

Consumes resolved VIA SDA/SCL edges, never firmware addresses or serial text.
"""


class LCD2004:
    offsets = (0x00, 0x40, 0x14, 0x54)

    def __init__(self):
        self.ddram = bytearray(b' ' * 128)
        self.address = 0
        self.four_bit = False
        self.high = None
        self.display_on = False
        self.backlight = False
        self.busy_until = 0
        self.timing_errors = 0
        self.commands = 0
        self.writes = 0

    def nibble(self, data, rs, now):
        if not self.four_bit:
            if not rs and data == 2:
                self.four_bit = True
                self.high = None
            return
        if self.high is None:
            self.high = (data, rs)
            return
        high, old_rs = self.high
        self.high = None
        value = high << 4 | data
        if old_rs != rs:
            return
        if now < self.busy_until:
            self.timing_errors += 1
            return
        self.busy_until = now + (2000 if not rs and value in (1, 2) else 40)
        if rs:
            self.ddram[self.address & 127] = value
            self.address = (self.address + 1) & 127
            self.writes += 1
        else:
            self.commands += 1
            if value == 1:
                self.ddram[:] = b' ' * 128
                self.address = 0
            elif value == 2:
                self.address = 0
            elif value & 0x80:
                self.address = value & 127
            elif value & 0xF8 == 8:
                self.display_on = bool(value & 4)
            elif value & 0xF0 == 0x30:
                self.four_bit = False

    @property
    def lines(self):
        if not self.display_on:
            return (' ' * 20,) * 4
        return tuple(bytes(self.ddram[o:o+20]).decode('ascii', errors='replace') for o in self.offsets)


class I2CBackpack:
    def __init__(self, address=0x27, present=True):
        if not 0x08 <= address <= 0x77:
            raise ValueError('I2C address must be a 7-bit peripheral address')
        self.address, self.present = address, present
        self.lcd = LCD2004()
        self.port = 255  # PCF8574 power-on weak-high ports
        self.reset_bus()
        self.starts = self.stops = self.acks = self.bytes_written = 0

    def reset_bus(self):
        """CPU/VIA reset releases the bus; external LCD power/state is retained."""
        self.sda = self.scl = 1
        self.pull_low = False
        self.phase = 'idle'
        self.value = self.bits = 0
        self.selected = False
        self.address_byte = True
        self.ack_stage = 0

    def drive(self, sda, scl, now):
        old_sda, old_scl = self.sda, self.scl
        if old_scl and scl and old_sda != sda and not self.pull_low:
            if not sda:
                self.starts += 1
                self.phase = 'receive'
                self.bits = self.value = 0
                self.address_byte = True
                self.selected = False
            else:
                self.stops += 1
                self.phase = 'idle'
                self.pull_low = False
        if not old_scl and scl:
            if self.phase == 'receive':
                self.value = (self.value << 1) | sda
                self.bits += 1
                if self.bits == 8:
                    if self.address_byte:
                        self.selected = self.present and self.value == self.address << 1
                        self.address_byte = False
                    elif self.selected:
                        self._write(self.value, now)
                    self.phase = 'ack'
                    self.ack_stage = 0
            elif self.phase == 'ack':
                self.ack_stage = 1
        if old_scl and not scl and self.phase == 'ack':
            if not self.ack_stage:
                self.pull_low = self.selected
                if self.selected:
                    self.acks += 1
            else:
                self.pull_low = False
                self.phase = 'receive'
                self.value = self.bits = 0
        self.sda, self.scl = sda, scl

    def _write(self, value, now):
        self.bytes_written += 1
        before, self.port = self.port, value
        self.lcd.backlight = bool(value & 8)
        if before & 4 and not value & 4 and not value & 2:
            self.lcd.nibble(value >> 4, value & 1, now)
