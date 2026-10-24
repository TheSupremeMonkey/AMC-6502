"""Host debugger: instruction-boundary execution and non-destructive inspection."""


class Debugger:
    def __init__(self, machine):
        self.machine = machine
        self.breakpoints = set()  # (zero-based bank or None for all banks, address)
        self.running = False
        self.reason = 'paused'
        self.remaining = None
        self._stopped_at = None
        self._skip_once = None
        self._stopped_generation = None

    def _location(self):
        return self.machine.bus.bank, self.machine.cpu.pc

    def _break_at(self, location):
        bank, pc = location
        return (bank, pc) in self.breakpoints or (None, pc) in self.breakpoints

    def resume(self, instructions=None):
        if instructions is not None and instructions < 1:
            raise ValueError('Instruction budget must be positive')
        self._skip_once = (self._stopped_at if self._stopped_at == self._location()
                           and self._stopped_generation == self.machine.reset_generation else None)
        self._stopped_at = None
        self.remaining = instructions
        self.running = True
        self.reason = 'running'

    def stop(self, reason='stopped'):
        self.running = False
        self.reason = reason
        self._skip_once = None
        if reason == 'breakpoint':
            self._stopped_at = self._location()
            self._stopped_generation = self.machine.reset_generation
        elif reason == 'reset' or self._stopped_at != self._location():
            self._stopped_at = None

    def run_chunk(self, instructions=1000):
        if instructions < 1:
            raise ValueError('Chunk size must be positive')
        executed = 0
        for _ in range(instructions):
            if not self.running:
                break
            # A breakpoint on the IRQ handler must see its first opcode, too.
            self.machine.prepare_instruction()
            location = self._location()
            if self._break_at(location) and location != self._skip_once:
                self.stop('breakpoint')
                break
            self._skip_once = None
            self.machine.step(prepare=False)
            executed += 1
            if self.remaining is not None:
                self.remaining -= 1
                if not self.remaining:
                    self.stop('slice')
                    break
        return executed

    def step(self, count=1):
        if not 1 <= count <= 10000:
            raise ValueError('Step count must be 1 through 10000')
        self.stop('step')
        self._stopped_at = None
        for _ in range(count):
            self.machine.step()

    def registers(self):
        cpu, bus = self.machine.cpu, self.machine.bus
        flags = ''.join(name if cpu.p & (1 << (7-i)) else '.'
                        for i, name in enumerate('NVUBDIZC'))
        return (f'{"RUNNING" if self.running else "PAUSED"} ({self.reason}) '
                f'BANK={bus.bank} PC=${cpu.pc:04X} A=${cpu.a:02X} X=${cpu.x:02X} '
                f'Y=${cpu.y:02X} SP=${cpu.sp:02X} P=${cpu.p:02X} [{flags}] '
                f'CYCLES={cpu.processorCycles}')

    def memory(self, address, length=64):
        if not 0 <= address <= 0xFFFF or not 1 <= length <= 4096 or address + length > 0x10000:
            raise ValueError('Memory range must fit $0000-$FFFF; length must be 1-4096')
        return bytes(self.machine.bus.peek(a) for a in range(address, address + length))

    def write_memory(self, address, values):
        values = list(values)
        if (not values or len(values) > 256 or not 0 <= address < 0x8000
                or address + len(values) > 0x8000 or any(not 0 <= v <= 255 for v in values)):
            raise ValueError('Write 1-256 bytes wholly within RAM $0000-$7FFF')
        for offset, value in enumerate(values):
            self.machine.bus[address + offset] = value
