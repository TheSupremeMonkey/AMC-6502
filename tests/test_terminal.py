"""Real subprocess checks for pipe handling, continuous stop, and SIGINT."""
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMAND = [str(ROOT / '.venv/bin/python'), '-m', 'emulator', '--paused']


class TerminalProcessTests(unittest.TestCase):
    def test_piped_debug_commands_and_memory_edit(self):
        result = subprocess.run(COMMAND, cwd=ROOT, input=(
            ':write 0400 A9 42 8D 00 03 4C 05 04\n'
            ':pc 0400\n:step 2\n:mem 0300 1\n:break 0405\n:continue\n'
            ':regs\n:delete all\n:step\n:quit\n'),
            text=True, capture_output=True, timeout=10, check=True)
        self.assertIn('0300: 42', result.stdout)
        self.assertIn('Breakpoint: PAUSED (breakpoint)', result.stdout)
        self.assertIn('PC=$0405', result.stdout)
        self.assertIn('All breakpoints cleared.', result.stdout)
        self.assertNotIn('Error:', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_continuous_execution_stops_with_command_and_ctrl_c(self):
        process = subprocess.Popen(COMMAND, cwd=ROOT, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = bytearray()

        def send(text):
            process.stdin.write(text.encode())
            process.stdin.flush()

        def wait_for(text, start=0):
            deadline = time.monotonic() + 10
            target = text.encode()
            while target not in output[start:]:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.fail(f'Timed out waiting for {text!r}: {output.decode(errors="replace")}')
                ready, _, _ = select.select([process.stdout], [], [], remaining)
                if not ready:
                    continue
                data = os.read(process.stdout.fileno(), 4096)
                if not data:
                    self.fail(f'Terminal exited unexpectedly: {output.decode(errors="replace")}')
                output.extend(data)
            return len(output)

        try:
            wait_for('host debugger')
            send(':write 0400 E8 4C 00 04\n:pc 0400\n:run\n')
            start = wait_for('Running;')
            send(':status\n')
            wait_for('RUNNING (running)', start)
            start = len(output)
            send(':stop\n')
            wait_for('PAUSED (stopped)', start)
            stopped = output[start:].decode()
            self.assertRegex(stopped, r'PC=\$040[01]')
            self.assertGreater(int(re.search(r'CYCLES=(\d+)', stopped).group(1)), 0)
            start = len(output)
            send(':run\n')
            wait_for('Running;', start)
            start = len(output)
            process.send_signal(signal.SIGINT)
            wait_for('PAUSED (Ctrl-C)', start)
            self.assertIsNone(process.poll())
            start = len(output)
            send(':step\n')
            wait_for('PAUSED (step)', start)
            send(':quit\n')
            _, errors = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0)
            self.assertEqual(errors, b'')
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()

    def test_default_terminal_boot_and_manual_bank_reset_capture(self):
        result = subprocess.run(COMMAND[:-1], cwd=ROOT, input=(
            ':bank 4\n:bank 3\n:bank 1\n:quit\n'),
            text=True, capture_output=True, timeout=30, check=True)
        self.assertIn('ALL CHECKS PASS', result.stdout)
        self.assertIn('BANK 2: WOZ MONITOR', result.stdout)
        self.assertEqual(result.stdout.count('BANK 0: MICROSOFT BASIC'), 2)
        self.assertEqual(result.stderr, '')
