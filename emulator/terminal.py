"""Command handling shared by the interactive loop and debugger tests."""
from emulator.debugger import Debugger

SLICE = 1000000
HELP = '''Host commands (addresses/bytes are hex; counts are decimal):
:run                 Run continuously; :stop or Ctrl-C pauses
:stop                Pause at an instruction boundary
:continue            Run up to 1,000,000 instructions, respecting breakpoints
:step [count]        Execute 1-10000 instructions, ignoring breakpoints
:regs                Pause and display CPU registers/flags
:status              Display state without pausing
:mem address [count] Pause; inspect 1-4096 bytes without I/O side effects
:write address bytes Pause; edit 1-256 RAM bytes (no ROM/device writes)
:pc address          Pause and set PC without resetting other CPU state
:break [addr [all]]  List/add breakpoint in current bank, or all banks
:delete addr [all]   Delete breakpoint; :delete all clears every breakpoint
:bank 1..4           Hold reset, set toggles to bank 0..3, then release reset
:lcd [off|mirror|dashboard] Inspect LCD, or request firmware display mode
:reset               Reset current bank; :quit exits
:help                Show this help
Other lines go to firmware as ASCII plus CR. Paused input runs one bounded slice.'''


def hex_number(token, maximum=0xFFFF):
    value = int(token.removeprefix('$').removeprefix('0x').removeprefix('0X'), 16)
    if not 0 <= value <= maximum:
        raise ValueError(f'Hex value must be between 0 and {maximum:X}')
    return value


class Terminal:
    def __init__(self, machine, emit=print):
        self.debugger = Debugger(machine)
        self.machine = machine
        self.emit = emit
        self.quit = False

    def handle(self, line):
        try:
            self._handle(line)
        except (ValueError, IndexError) as error:
            self.emit(f'Error: {error}')

    def _handle(self, line):
        d, m = self.debugger, self.machine
        if not line.startswith(':'):
            try:
                data = line.encode('ascii')
            except UnicodeEncodeError:
                raise ValueError('Firmware console accepts ASCII only') from None
            m.bus.serial.feed(data + b'\r')
            if not d.running:
                d.resume(SLICE)
            return
        args = line.split()
        command, args = args[0], args[1:]
        if command == ':help' and not args:
            self.emit(HELP)
        elif command == ':quit' and not args:
            d.stop()
            self.quit = True
        elif command == ':lcd' and len(args) <= 1:
            if args:
                modes = {'off': 0, 'mirror': 1, 'dashboard': 2}
                if args[0] not in modes:
                    raise ValueError('Use :lcd off, :lcd mirror, :lcd dashboard, or :lcd')
                m.bus.ram[0x02FD] = modes[args[0]]
                # A documented firmware mailbox, serviced by console polling.
                # Do not call a firmware PC, write the device, or fabricate text.
                if not d.running:
                    d.resume(SLICE)
                self.emit('LCD mode requested; firmware applies it at a console service point.')
            else:
                self.emit('LCD 20x4 (firmware mode %d, I2C error %d):' %
                          (m.bus.ram[0x7FD8], m.bus.ram[0x7FD7]))
                self.emit('+' + '-' * 20 + '+')
                for row in m.bus.backpack.lcd.lines:
                    self.emit('|' + row + '|')
                self.emit('+' + '-' * 20 + '+')
        elif command == ':run' and not args:
            d.resume()
            self.emit('Running; :stop or Ctrl-C pauses.')
        elif command == ':continue' and not args:
            d.resume(SLICE)
        elif command == ':stop' and not args:
            d.stop()
            self.emit(d.registers())
        elif command in (':regs', ':status') and not args:
            if command == ':regs':
                d.stop()
            self.emit(d.registers())
        elif command == ':step' and len(args) <= 1:
            d.step(int(args[0]) if args else 1)
            self.emit(d.registers())
        elif command == ':mem' and 1 <= len(args) <= 2:
            address = hex_number(args[0])
            length = int(args[1]) if len(args) == 2 else 64
            d.stop()
            data = d.memory(address, length)
            for offset in range(0, len(data), 16):
                part = data[offset:offset+16]
                ascii_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in part)
                self.emit(f'{address+offset:04X}: {" ".join(f"{b:02X}" for b in part):47} |{ascii_text}|')
        elif command == ':write' and len(args) >= 2:
            address = hex_number(args[0])
            values = [hex_number(value, 255) for value in args[1:]]
            d.stop()
            d.write_memory(address, values)
            self.emit(f'Wrote {len(values)} RAM byte(s) at ${address:04X}.')
        elif command == ':pc' and len(args) == 1:
            address = hex_number(args[0])
            d.stop()
            m.cpu.pc = address
            self.emit(d.registers())
        elif command in (':break', ':delete'):
            if command == ':break' and not args:
                if not d.breakpoints:
                    self.emit('No breakpoints.')
                for bank, address in sorted(d.breakpoints, key=lambda b: (-1 if b[0] is None else b[0], b[1])):
                    self.emit(f'${address:04X} bank {"all" if bank is None else bank}')
            elif command == ':delete' and args == ['all']:
                d.breakpoints.clear()
                self.emit('All breakpoints cleared.')
            elif 1 <= len(args) <= 2 and (len(args) == 1 or args[1] == 'all'):
                address = hex_number(args[0])
                bank = None if len(args) == 2 else m.bus.bank
                key = (bank, address)
                if command == ':break':
                    d.breakpoints.add(key)
                    self.emit(f'Breakpoint ${address:04X} bank {"all" if bank is None else bank}.')
                else:
                    d.breakpoints.discard(key)
                    self.emit('Breakpoint removed.')
            else:
                raise ValueError('Use :break [address [all]], :delete address [all], or :delete all')
        elif command == ':bank' and len(args) == 1:
            choice = int(args[0])
            if choice not in range(1, 5):
                raise ValueError('Bank choice must be 1 through 4')
            m.select_bank(choice - 1)
            d.stop('reset')
            d.resume(SLICE)
        elif command == ':reset' and not args:
            m.reset()
            d.stop('reset')
            d.resume(SLICE)
        else:
            raise ValueError('Unknown command or arguments; use :help')
