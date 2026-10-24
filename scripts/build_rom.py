"""Build original-source ports and pack four 16 KB banks."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
CA = ROOT / '.tools/cc65/bin/ca65'
LD = ROOT / '.tools/cc65/bin/ld65'
BANK_INFO_OFFSET = 0x1FC0  # $FFC0 relative to the shared $E000 window
BANK_INFO_SIZE = 32
BANK_DESCRIPTIONS = (
    'BANK 0: MICROSOFT BASIC',
    'BANK 1: RESERVED',
    'BANK 2: WOZ MONITOR',
    'BANK 3: HARDWARE DIAGNOSTICS',
)


def assemble(name, source, config, includes=(), defines=()):
    obj = BUILD / f'{name}.o'
    subprocess.run([str(CA), '--cpu', '6502', '-g', '-l', str(BUILD / f'{name}.lst'),
                    *[v for p in includes for v in ('-I', str(p))],
                    *[v for d in defines for v in ('-D', d)], '-o', str(obj), str(source)], check=True)
    subprocess.run([str(LD), '-C', str(config), '-m', str(BUILD / f'{name}.map'),
                    '-Ln', str(BUILD / f'{name}.lbl'), '-o', str(BUILD / f'{name}.bin'), str(obj)], check=True)
    return (BUILD / f'{name}.bin').read_bytes()


def build():
    BUILD.mkdir(exist_ok=True)
    stage = BUILD / 'basic-source'
    shutil.copytree(ROOT / '.tools/msbasic', stage, ignore=shutil.ignore_patterns('.git', 'orig'), dirs_exist_ok=True)
    config = (stage / 'defines_osi.s').read_text().replace('$FFEB', 'FW_CIN').replace('$FFEE', 'FW_COUT')
    config = config.replace('$FFF4', 'SYNERR').replace('$FFF7', 'SYNERR')
    (stage / 'defines_osi.s').write_text(config)
    # Limit BASIC's memory probe and explicit size input before kernel LCD RAM.
    init = (stage / 'init.s').read_text()
    init = init.replace('L40DD:\n', 'L40DD:\n        lda LINNUM+1\n        cmp #>FW_USER_END\n        bcc @amc_probe\n        bne L40FA\n        lda LINNUM\n        cmp #<FW_USER_END\n        bcs L40FA\n@amc_probe:\n')
    init = init.replace('L40FA:\n', 'L40FA:\n        lda LINNUM+1\n        cmp #>FW_USER_END\n        bcc @amc_size\n        bne @amc_clamp\n        lda LINNUM\n        cmp #<FW_USER_END\n        bcc @amc_size\n@amc_clamp:\n        lda #<FW_USER_END\n        sta LINNUM\n        lda #>FW_USER_END\n        sta LINNUM+1\n@amc_size:\n')
    (stage / 'init.s').write_text(init)
    (stage / 'msbasic.s').write_text('.include "fw.inc"\n' + (stage / 'msbasic.s').read_text())
    with (stage / 'zeropage.s').open('a') as stream:
        stream.write('\n.assert RNDSEED+BYTES_FP <= FW_STRPTR, error, "BASIC overlaps kernel zero page"\n')
        stream.write('.assert RAMSTART2 >= $0300, error, "BASIC overlaps kernel page-2 workspace"\n')
    (stage / 'header.s').write_text('.segment "HEADER"\n jmp COLD_START\n')
    # No keyboard IRQ/break scanner yet: do not consume serial input here.
    (stage / 'osi_iscntc.s').write_text('.segment "CODE"\nISCNTC:\n rts\n')
    cfg = (stage / 'osi.cfg').read_text().replace('$A000', '$C000').replace('$3F00', '$2000').replace('fill = no', 'fill = yes, fillval = $FF')
    (BUILD / 'basic.cfg').write_text(cfg)
    basic = assemble('basic', stage / 'msbasic.s', BUILD / 'basic.cfg', [stage, ROOT / 'firmware/include'], ['osi'])
    source = (ROOT / '.tools/tranter6502/asm/wozmon/wozmon.s').read_text()
    source = '.include "fw.inc"\n' + source[:source.index('; Interrupt Vectors')]
    source = source.replace('.org $FF00', '.setcpu "6502"\n.segment "CODE"')
    start = source.index('RESET:')
    end = source.index('NOTCR:', start)
    source = source[:start] + 'RESET:          CLD\n                SEI\n                LDY #$7F\n' + source[end:]
    source = source.replace('LDA KBDCR       ; Key ready?\n                BPL NEXTCHAR    ; Loop until ready.\n                LDA KBD', 'JSR $E103\n                ORA #$80        ; Woz parser expects high-bit ASCII.\n                NOP')
    start = source.index('ECHO:')
    source = source[:start] + 'ECHO:           PHA\n                AND #$7F\n                JSR $E100\n                PLA\n                RTS\n'
    # Relocation expands branches; ca65 reports any overflow.
    source = source.replace('JSR $E103', 'JSR FW_CIN').replace('JSR $E100', 'JSR FW_COUT')
    (BUILD / 'wozmon.s').write_text(source)
    shutil.copy(ROOT / 'firmware/payload.cfg', BUILD / 'payload.cfg')
    woz = assemble('wozmon', BUILD / 'wozmon.s', BUILD / 'payload.cfg', [ROOT / 'firmware/include'])
    kernel = assemble('kernel', ROOT / 'firmware/kernel.s', ROOT / 'firmware/kernel.cfg', [ROOT / 'firmware/include'])
    (BUILD / 'placeholder.s').write_text('.setcpu "6502"\n.segment "CODE"\nloop: jmp loop\n')
    placeholder = assemble('placeholder', BUILD / 'placeholder.s', BUILD / 'payload.cfg')
    diagnostics = assemble('diagnostics', ROOT / 'firmware/diagnostics.s', BUILD / 'payload.cfg', [ROOT / 'firmware/include'])
    assert all(len(x) == 8192 for x in (basic, woz, kernel, placeholder, diagnostics))
    banks = []
    if kernel[BANK_INFO_OFFSET:BANK_INFO_OFFSET + BANK_INFO_SIZE] != bytes(BANK_INFO_SIZE):
        raise ValueError('Kernel metadata reservation does not match builder layout')
    for payload, description in zip((basic, placeholder, woz, diagnostics), BANK_DESCRIPTIONS):
        text = description.encode('ascii')
        if len(text) >= BANK_INFO_SIZE:
            raise ValueError('Bank description must fit with a null terminator')
        upper = bytearray(kernel)
        upper[BANK_INFO_OFFSET:BANK_INFO_OFFSET + BANK_INFO_SIZE] = text.ljust(BANK_INFO_SIZE, b'\0')
        banks.append(payload + upper)
    image = b''.join(banks)
    (BUILD / 'amc6502.bin').write_bytes(image)
    shutil.copy(ROOT / 'docs/FIRMWARE.md', BUILD / 'FIRMWARE-SOURCES.md')
    shutil.copy(ROOT / '.tools/BASIC-M6502/LICENSE', BUILD / 'MICROSOFT-LICENSE.txt')
    shutil.copy(ROOT / '.tools/msbasic/README.md', BUILD / 'MSBASIC-UPSTREAM-README.md')
    shutil.copy(ROOT / '.tools/tranter6502/README', BUILD / 'WOZ-UPSTREAM-README.md')
    print(f'Built {len(image)} bytes: BASIC / reserved / Woz Monitor / diagnostics; shared upper firmware with bank-specific description records')


if __name__ == '__main__':
    build()
