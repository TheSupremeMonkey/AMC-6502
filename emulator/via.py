"""Classic 6522 ports, interval timers, and interrupt control.

Integer PHI2 timing; no shift engine or CA2/CB2 output handshake sequencer.
See docs/VIA.md for register semantics and timing approximations.
"""


class VIA6522:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ora = self.orb = self.ddra = self.ddrb = 0
        self.input_a = self.input_b = self.latched_a = self.latched_b = 0xFF
        self.acr = self.pcr = self.ifr = self.ier = self.sr = 0
        self.t1_latch = self.t2_latch = 0
        self.t1_counter = self.t2_counter = 0xFFFF
        self.t1_running = self.t2_running = False
        self.t1_armed = self.t2_armed = False
        self.t1_delay = self.t2_delay = 0
        self.pb7 = 1
        self.lines = dict.fromkeys(('ca1', 'ca2', 'cb1', 'cb2'), 1)

    @property
    def irq(self):
        return bool(self.ifr & self.ier & 0x7F)

    @property
    def pins_a(self):
        return (self.ora & self.ddra) | (self.input_a & ~self.ddra & 0xFF)

    @property
    def pins_b(self):
        output = self.orb
        if self.acr & 0x80 and self.ddrb & 0x80:
            output = (output & 0x7F) | self.pb7 << 7
        return (output & self.ddrb) | (self.input_b & ~self.ddrb & 0xFF)

    def set_port_a(self, value):
        self.input_a = value & 0xFF

    def set_port_b(self, value):
        before = self.pins_b
        self.input_b = value & 0xFF
        self._pb6_edge(before)

    def _pb6_edge(self, before):
        if self.acr & 0x20 and before & 0x40 and not self.pins_b & 0x40:
            self._advance_t2(1, pulse=True)

    def set_control(self, line, level):
        if line in ('ca2', 'cb2'):
            mode = (self.pcr >> (1 if line == 'ca2' else 5)) & 7
            if mode >= 4:
                return  # configured output; external stimulus cannot drive it
        before = self.lines[line]
        level = int(bool(level))
        self.lines[line] = level
        if before == level:
            return
        if line in ('ca1', 'cb1'):
            port_a = line == 'ca1'
            positive = bool(self.pcr & (1 if port_a else 0x10))
            if level == positive:
                self.ifr |= 2 if port_a else 0x10
                if port_a and self.acr & 1:
                    self.latched_a = self.input_a
                elif not port_a and self.acr & 2:
                    self.latched_b = self.input_b
        else:
            mode = (self.pcr >> (1 if line == 'ca2' else 5)) & 7
            if mode < 4 and level == bool(mode & 2):
                self.ifr |= 1 if line == 'ca2' else 8

    def _ack_port(self, port_a):
        self.ifr &= ~(2 if port_a else 0x10)
        mode = (self.pcr >> (1 if port_a else 5)) & 7
        if mode in (0, 2):  # dependent input mode; independent flags persist
            self.ifr &= ~(1 if port_a else 8)

    def read(self, register, *, side_effects=True, input_a=None):
        r = register & 15
        if r in (1, 15):
            if r == 1 and side_effects:
                self._ack_port(True)
            inputs = self.latched_a if self.acr & 1 else (self.input_a if input_a is None else input_a)
            return (self.ora & self.ddra) | (inputs & ~self.ddra & 0xFF)
        if r == 0:
            if side_effects:
                self._ack_port(False)
            inputs = self.latched_b if self.acr & 2 else self.input_b
            return (self.pins_b & self.ddrb) | (inputs & ~self.ddrb & 0xFF)
        if r == 2:
            return self.ddrb
        if r == 3:
            return self.ddra
        if r == 4:
            if side_effects:
                self.ifr &= ~0x40
            return self.t1_counter & 0xFF
        if r == 5:
            return self.t1_counter >> 8
        if r in (6, 7):
            return self.t1_latch >> (8 if r == 7 else 0) & 0xFF
        if r == 8:
            if side_effects:
                self.ifr &= ~0x20
            return self.t2_counter & 0xFF
        if r == 9:
            return self.t2_counter >> 8
        if r == 10:
            if side_effects:
                self.ifr &= ~4
            return self.sr
        if r == 11:
            return self.acr
        if r == 12:
            return self.pcr
        if r == 13:
            return self.ifr | (0x80 if self.irq else 0)
        return self.ier | 0x80

    def write(self, register, value):
        r, value = register & 15, value & 0xFF
        before_b = self.pins_b
        if r in (1, 15):
            self.ora = value
            if r == 1:
                self._ack_port(True)
        elif r == 0:
            self.orb = value
            self._ack_port(False)
        elif r == 2:
            self.ddrb = value
        elif r == 3:
            self.ddra = value
        elif r in (4, 6):
            self.t1_latch = (self.t1_latch & 0xFF00) | value
        elif r in (5, 7):
            self.t1_latch = (value << 8) | (self.t1_latch & 0xFF)
            self.ifr &= ~0x40
            if r == 5:
                self.t1_counter = self.t1_latch
                self.t1_running = self.t1_armed = True
                self.t1_delay = 1
                self.pb7 = 0
        elif r == 8:
            self.t2_latch = value
        elif r == 9:
            self.t2_counter = value << 8 | self.t2_latch
            self.t2_running = self.t2_armed = True
            self.t2_delay = 0 if self.acr & 0x20 else 1
            self.ifr &= ~0x20
        elif r == 10:
            self.sr = value
            self.ifr &= ~4
        elif r == 11:
            if value & 0x1C:
                raise NotImplementedError('6522 shift-register modes are not implemented')
            self.acr = value
        elif r == 12:
            modes = ((value >> 1) & 7, (value >> 5) & 7)
            if any(mode in (4, 5) for mode in modes):
                raise NotImplementedError('6522 CA2/CB2 output handshake/pulse modes are not implemented')
            self.pcr = value
            for line, mode in zip(('ca2', 'cb2'), modes):
                if mode >= 6:
                    self.lines[line] = int(mode == 7)
        elif r == 13:
            self.ifr &= ~(value & 0x7F)
        elif r == 14:
            if value & 0x80:
                self.ier |= value & 0x7F
            else:
                self.ier &= ~(value & 0x7F)

        if r in (0, 2):
            self._pb6_edge(before_b)

    def tick(self, cycles):
        if cycles < 0:
            raise ValueError('Cannot advance VIA by negative cycles')
        remaining = cycles
        while self.t1_running and remaining:
            if self.t1_delay:
                elapsed = min(remaining, self.t1_delay)
                self.t1_delay -= elapsed
                remaining -= elapsed
                if not remaining:
                    break
            until = self.t1_counter + 1
            if remaining < until:
                self.t1_counter -= remaining
                break
            remaining -= until
            if self.t1_armed:
                self.ifr |= 0x40
                if self.acr & 0x40:
                    self.pb7 ^= 1
                else:
                    self.pb7 = 1
                    self.t1_armed = False
            if self.acr & 0x40:
                self.t1_counter = self.t1_latch
                self.t1_delay = 1
            else:
                self.t1_counter = 0xFFFF
        if not self.acr & 0x20:
            self._advance_t2(cycles)

    def _advance_t2(self, cycles, pulse=False):
        if not self.t2_running:
            return
        if not pulse and self.t2_delay:
            elapsed = min(cycles, self.t2_delay)
            self.t2_delay -= elapsed
            cycles -= elapsed
        if cycles > self.t2_counter and self.t2_armed:
            self.ifr |= 0x20
            self.t2_armed = False
        self.t2_counter = (self.t2_counter - cycles) & 0xFFFF
