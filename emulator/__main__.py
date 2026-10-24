"""Line-oriented firmware terminal with an instruction-boundary host debugger."""
import argparse
from collections import deque
import os
from pathlib import Path
import select
import signal
import sys

from emulator.machine import Machine
from emulator.terminal import SLICE, Terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', nargs='?', default='build/amc6502.bin')
    parser.add_argument('--paused', action='store_true', help='start at reset vector without executing')
    parser.add_argument('--bank', type=int, choices=range(4), default=0,
                        help='initial bank toggle setting, 0 through 3')
    args = parser.parse_args()
    machine = Machine(Path(args.rom).read_bytes(), bank=args.bank)
    if machine.bus.legacy:
        parser.error('Terminal requires the 64 KB banked image')
    terminal = Terminal(machine, lambda text: print(text, flush=True))
    debugger = terminal.debugger
    print('AMC-6502 host debugger — :help for commands; Ctrl-C pauses; :quit exits.', flush=True)
    if not args.paused:
        debugger.resume(SLICE)
    captured, generation, previous_cr = 0, machine.reset_generation, False
    pending = deque()
    buffer = ''
    eof = False
    stop_requested = False

    def request_stop(_signum, _frame):
        # Do not raise KeyboardInterrupt in the middle of a CPU/device update.
        nonlocal stop_requested
        stop_requested = True

    old_handler = signal.signal(signal.SIGINT, request_stop)

    def flush_serial():
        nonlocal captured, generation, previous_cr
        if generation != machine.reset_generation:
            captured, generation, previous_cr = 0, machine.reset_generation, False
        output = machine.bus.serial.output
        text = []
        for value in output[captured:]:
            if value == 13:
                text.append('\n')
            elif value == 10:
                if not previous_cr:
                    text.append('\n')
            else:
                text.append(chr(value) if value < 128 else '\ufffd')
            previous_cr = value == 13
        captured = len(output)
        if text:
            sys.stdout.write(''.join(text))
            sys.stdout.flush()

    try:
        while not terminal.quit:
            if stop_requested:
                stop_requested = False
                debugger.stop('Ctrl-C')
                print('\n' + debugger.registers(), flush=True)
            # Read raw stdin bytes to avoid TextIO read-ahead hiding piped lines.
            if not eof:
                ready, _, _ = select.select([sys.stdin.fileno()], [], [], 0 if debugger.running or pending else 0.1)
                if ready:
                    data = os.read(sys.stdin.fileno(), 4096)
                    if not data:
                        eof = True
                        if buffer:
                            pending.append(buffer.rstrip('\r'))
                            buffer = ''
                    else:
                        buffer += data.decode('utf-8', errors='replace')
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            pending.append(line.rstrip('\r'))
            # Preserve batch command order: finite slices finish before the next
            # input line. Stop remains responsive; continuous run accepts input.
            if pending and (not debugger.running or debugger.remaining is None
                            or pending[0].strip() == ':stop'):
                terminal.handle(pending.popleft())
                flush_serial()
            if terminal.quit:
                break
            if debugger.running:
                try:
                    debugger.run_chunk(1000)
                except (NotImplementedError, ValueError) as error:
                    debugger.stop('execution error')
                    print(f'Execution stopped: {error}', flush=True)
                flush_serial()
                if not debugger.running and debugger.reason == 'breakpoint':
                    print('\nBreakpoint: ' + debugger.registers(), flush=True)
            if eof and not pending and (not debugger.running or debugger.remaining is None):
                break
    finally:
        signal.signal(signal.SIGINT, old_handler)


if __name__ == '__main__':
    main()
