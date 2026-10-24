# Bank 3 hardware diagnostics

Build/run with `make run`, then enter `:bank 4` to set bank 3 under reset. Diagnostics start automatically through the shared serial console.

Expected report:

```text
AMC-6502 DIAGNOSTICS - BANK 3
PASS RAM $0300-$7F7F (restored)
VIA 1
PASS T1 + IRQ
PASS T2 + IRQ
VIA 2
PASS T1 + IRQ
PASS T2 + IRQ
ALL CHECKS PASS
R to rerun / L load HEX
Hold RESET, set bank toggles, release RESET to change ROM.
```

Enter `R` to repeat checks, `L` to load HEX, or `:reset` to reboot diagnostics. Use `:bank 1` for BASIC or `:bank 3` for Woz. Numeric keys have no bank action. Serial-only completion fits the terminal’s 1,000,000-instruction slice; LCD mirroring can require `:continue` or `:run` because scrolling redraws the display.

## Checks and side effects

`firmware/diagnostics.s` occupies the bank's lower 8 KB. It uses common PUTS from the [shared firmware API](FIRMWARE-API.md) plus the console routines at `$E100`/`$E103` and a shared IRQ dispatch vector, keeping all four upper halves identical except for bank-description metadata at `$FFC0–$FFDF`.

- **RAM:** read/save a byte, write/read `$AA` and `$55`, then restore the saved byte immediately, for every address `$0300–$7F7F`. On a mismatch, attempt restoration, report failure, and continue with VIA checks. These patterns exercise both values of every data bit; this is not an address-alias, retention, or exhaustive RAM qualification test.
- **VIA timers/IRQ:** for each VIA, test T1 and T2 one-shot operation. Verify the timeout flag sets while the source is disabled, then enable it and verify the CPU reaches the diagnostic's IRQ handler. The handler acknowledges timer flags. Each wait is bounded, so missing flags or missing interrupts report failure rather than hanging. Interrupts are masked while printing so the software serial timing remains intact.
- **Summary:** print `ALL CHECKS PASS` only if RAM and all four timer/IRQ checks pass. Otherwise print `DIAGNOSTIC FAILURE`; individual lines identify the failing check. RAM failure currently identifies the tested range rather than the exact failing byte.

Workspace is deliberately not preserved: zero-page `$00–$05`, diagnostic scratch `$02F4–$02F8`, shared string pointer `$F0–$F1`, shared console scratch `$02F0–$02F1`, shared IRQ hook `$02F2–$02F3`, and the active CPU stack. Existing BASIC workspace cannot be resumed as a session after a bank reset. The RAM region under test is restored in healthy hardware; a physical stuck bit can prevent restoration.

The VIA checks reset ACR modes, clear/disable interrupt sources, and program timer counters. They do not drive expansion port pins or change expansion DDRs. Counters can continue wrapping after their one-shot event, with interrupt sources disabled on completion. No external loopback, keyboard, LCD, ROM checksum, clock measurement, bank-display, or power/electrical checks are performed. The test validates nominal firmware-visible operation; passing in the emulator does not qualify physical chips or high-frequency operation. Current serial drivers target 1 MHz only.

## Shared IRQ hook

The common kernel's hardware IRQ entry jumps indirectly through RAM `$02F2–$02F3`. On every reset, before entering a payload, the kernel initializes that hook to its own default RTI handler. Bank 3 installs its acknowledging handler while SEI masks interrupts, then enables interrupts only during bounded timer checks. The diagnostic handler preserves A and does not modify X/Y. NMI continues to use a separate default RTI target and does not dispatch through this hook.

BASIC and Woz Monitor continue to start with interrupts masked; switching away from diagnostics resets the hook and devices. A payload installing another hook must do so with interrupts masked, provide a real handler that acknowledges its sources, and preserve any registers its foreground code needs. The hook is a provisional common firmware ABI.

## Automated validation

`make test` covers a normal run with seeded RAM restored byte-for-byte, rerun, and exit/reset back to BASIC. Fault injection separately supplies stuck RAM, stopped VIA timers, and suppressed VIA IRQ output; the actual ROM must report failures within its bounded run. Existing tests verify the 64 KB image size, shared halves identical outside the metadata field, and BASIC/Woz operation after kernel changes.

`L` enters the shared [serial RAM loader](SERIAL-LOADER.md). EOF or ESC returns to the diagnostics menu without rerunning tests.

Current schematic migration (2026-10-23): VIA1 `$7F80–$8FFF`, VIA2 `$B800–$BFFF`, repeated 16-register aliases; PA0 TX/PA1 RX. Manual bank toggles plus reset replace software selection. `$E106` returns carry set; `$8020` is unpopulated expansion. See [ROM switching](ROM-SWITCHING.md). LCD remains deferred.

LCD reserves `$7F80–$7FFF`; this area is excluded from user uploads and restoring diagnostics. See [LCD.md](LCD.md).

When dashboard mode is active, rerunning diagnostics updates its status row from testing to the actual PASS/FAIL summary. Serial reports remain unchanged.
