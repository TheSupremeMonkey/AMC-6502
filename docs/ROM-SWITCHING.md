# Changing ROM banks

The board has two bank toggles and a separate reset button. Hold RESET, set the toggles, wait for contacts to settle, then release RESET. The display identifies banks 0–3. Reset alone keeps the selected bank; power-on follows toggle positions.

| Bank | EEPROM A15 / A14 | Personality | Emulator command |
| --- | --- | --- | --- |
| 0 | 0 / 0 | Microsoft BASIC | `:bank 1` |
| 1 | 0 / 1 | Reserved | `:bank 2` |
| 2 | 1 / 0 | Woz Monitor | `:bank 3` |
| 3 | 1 / 1 | Diagnostics | `:bank 4` |

Host commands work in any personality. `:bank` requires an explicit choice; it simulates the complete reset/toggle procedure. `:reset` restarts the current bank. RAM is retained, but startup code may initialize workspace.

There is no software bank-switch register. `$8020` is an unpopulated expansion address; BASIC POKE or Woz writes there are ignored, not ROM selection. The old `$E106` entry stays in the service table as a retired service returning carry set. Diagnostic number keys no longer select banks. `FW_BANK_GET` obtains the bank from active ROM metadata.

Start with selected toggles using `.venv/bin/python -m emulator --bank 2` (zero-based).

Python: `Machine(image, bank=2)` starts with Woz selected; `select_bank(3)` performs the host reset/switch operation. `set_bank_switches(3)` changes mapping without reset and is available for testing raw external switch behavior. Do not continue execution across arbitrary switch changes when testing normal operation.
