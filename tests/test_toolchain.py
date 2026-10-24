"""End-to-end toolchain checks using upstream CPU and flat memory only."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from py65.devices.mpu6502 import MPU

ROOT = Path(__file__).resolve().parents[1]


class ToolchainTests(unittest.TestCase):
    def test_rom_boots_and_writes_result(self):
        rom = (ROOT / "build/toolchain-smoke.bin").read_bytes()
        self.assertEqual(len(rom), 8192)
        memory = [0] * 65536
        memory[0xE000:] = rom
        cpu = MPU(memory=memory, pc=None)
        self.assertEqual(cpu.pc, 0xE000)
        for _ in range(32):
            cpu.step()
        self.assertEqual(memory[0x0200], 0x42)
        self.assertEqual(cpu.a, 0x42)
        self.assertGreater(cpu.processorCycles, 0)

    def test_assembler_rejects_cmos_instruction(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cmos.s"
            source.write_text(".segment \"CODE\"\n stz $0200\n")
            result = subprocess.run(
                [str(ROOT / ".tools/cc65/bin/ca65"), "--cpu", "6502",
                 "-o", str(Path(directory) / "cmos.o"), str(source)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
