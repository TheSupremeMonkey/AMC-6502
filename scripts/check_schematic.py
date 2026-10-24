"""Export and run native KiCad ERC on the editable schematic sources."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
source = root / 'hardware/kicad/AMC-6502.kicad_sch'
out = root / 'build/schematic'
out.mkdir(parents=True, exist_ok=True)
for args in (
    ['sch', 'erc', '--format', 'json', '--exit-code-violations', '-o', str(out/'erc.json')],
    ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(out/'AMC-6502.xml')],
    ['sch', 'export', 'pdf', '-o', str(out/'AMC-6502.pdf')],
):
    subprocess.run(['kicad-cli', *args, str(source)], cwd=root, check=True)
report = json.loads((out/'erc.json').read_text())
assert not any(s['violations'] for s in report['sheets']), 'ERC violations'
netlist = ET.parse(out/'AMC-6502.xml').getroot()
nets = {(node.attrib['ref'], node.attrib['pin']): net.attrib['name'].split('/')[-1]
        for net in netlist.findall('./nets/net') for node in net.findall('node')}
expected = {
    ('U1','40'): 'RESET_N', ('U8','34'): 'RESET_N', ('U9','34'): 'RESET_N',
    ('U2','20'): 'A15', ('U2','27'): 'RAM_WE_N',
    ('U3','20'): 'ROM_CE_N', ('U3','27'): 'BANK0', ('U3','1'): 'BANK1',
    ('U8','23'): 'VIA1_CS_N', ('U9','23'): 'VIA2_CS_N',
    ('U8','2'): 'SER_TX', ('U8','3'): 'SER_RX',
    ('U4','1'): 'A11', ('U4','2'): 'A12', ('U4','3'): 'A13',
    ('U4','4'): 'A14', ('U4','5'): 'GND', ('U4','6'): 'A15',
    ('U4','7'): 'VIA2_CS_N', ('U4','8'): 'GND', ('U4','9'): 'VIA1_CS_N',
    ('U6','12'): 'A15', ('U6','13'): 'A14', ('U6','11'): 'ROM_CE_N',
    ('J9','5'): 'VIA1_CA1', ('J9','6'): 'VIA1_CA2',
}
for pin, net in expected.items():
    assert nets.get(pin) == net, f'{pin}: expected {net}, got {nets.get(pin)}'
print(f'ERC: zero violations; {len(expected)} key pin connections verified. PDF: {out / "AMC-6502.pdf"}')

# Evaluate the actual exported LS138/LS00/LS21 pin connectivity for all eight
# address slots' upper-bit combinations and control-signal states.
# This catches a correct-looking label wired to the wrong physical package pin.
def pin_net(ref, pin):
    return nets[(ref, str(pin))]


def check_logic(address, rw, phi2, reset):
    values = {'+5V': 1, 'GND': 0, 'R_W': rw, 'PHI2': phi2, 'RESET_N': reset}
    values.update({f'A{i}': (address >> i) & 1 for i in range(16)})
    read = lambda ref, pin: values[pin_net(ref, pin)]
    enabled = read('U4', 6) and not read('U4', 4) and not read('U4', 5)
    selected = read('U4', 1) | read('U4', 2) << 1 | read('U4', 3) << 2
    for i, pin in enumerate((15, 14, 13, 12, 11, 10, 9, 7)):
        values[pin_net('U4', pin)] = int(not (enabled and i == selected))
    gates = [
        ('U6', (1, 2), 3, True), ('U6', (4, 5), 6, True),
        ('U6', (9, 10), 8, True), ('U6', (12, 13), 11, True),
        ('U5', (1, 2, 4, 5), 6, False), ('U5', (9, 10, 12, 13), 8, False),
    ]
    for _ in range(4):
        for ref, inputs, output, invert in gates:
            if all(pin_net(ref, p) in values for p in inputs):
                state = int(all(read(ref, p) for p in inputs))
                values[pin_net(ref, output)] = 1-state if invert else state
    actual = (not read('U2', 20), not read('U3', 20),
              bool(read('U8', 24) and not read('U8', 23)),
              bool(read('U9', 24) and not read('U9', 23)))
    wanted = (address < 0x8000, address >= 0xC000,
              0xB000 <= address < 0xB800, 0xB800 <= address < 0xC000)
    assert actual == wanted, (hex(address), actual, wanted)
    assert read('U2', 22) == 1-rw
    assert read('U3', 22) == 1-rw
    assert read('U2', 27) == int(not (phi2 and reset and not rw))
    for i in range(6):
        assert values[f'EXP{i}_N'] == int(not (0x8000+i*0x800 <= address < 0x8800+i*0x800))


for block in range(32):
    for controls in range(8):
        check_logic(block*0x800, controls&1, controls>>1&1, controls>>2&1)
print('Native netlist decode/read/write truth table: 256 combinations pass.')
