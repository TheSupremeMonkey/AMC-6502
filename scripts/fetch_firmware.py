"""Fetch immutable upstream source checkouts; never overwrite local changes."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'msbasic': ('https://github.com/mist64/msbasic.git', '2a0bc2fe0db13f8cf1b5c40b1d5617263cdb9cb4'),
    'BASIC-M6502': ('https://github.com/microsoft/BASIC-M6502.git', '7460af2c03ae19c0e60ff327489229d2005b9357'),
    'tranter6502': ('https://github.com/jefftranter/6502.git', '0d20e5964544ccd8386ca21e562b49cb6b6a64d0'),
}


def fetch():
    (ROOT / '.tools').mkdir(exist_ok=True)
    for name, (url, revision) in SOURCES.items():
        path = ROOT / '.tools' / name
        if not path.exists():
            subprocess.run(['git', 'clone', '--no-checkout', url, str(path)], check=True)
            subprocess.run(['git', '-C', str(path), 'checkout', '--detach', revision], check=True)
        actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True)
        if actual != revision or dirty:
            raise SystemExit(f'{path}: expected clean source at {revision}; checkout left untouched')
        print(f'{name}: {revision}')


if __name__ == '__main__':
    fetch()
