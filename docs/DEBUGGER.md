# Terminal debugger

The debugger is an emulator-side tool. It uses no ROM space and does not add firmware instructions or hardware requirements.

## Start and run

```sh
make run
```

By default the emulator runs a bounded startup slice (1,000,000 instructions), displays serial output, then pauses for the next line. Ordinary ASCII lines are sent to firmware with CR; when paused, they start another bounded slice. This preserves BASIC/Woz/diagnostic interaction.

Use `:run` for continuous execution. Firmware continues while the host accepts input. `:stop` or **Ctrl-C** pauses without resetting CPU, RAM, peripherals, or selected bank. `:quit` exits; Ctrl-C no longer exits. EOF exits after pending finite command slices finish; it ends a continuous run once queued commands are consumed.

To start before executing the reset handler:

```sh
.venv/bin/python -m emulator --paused
```

An alternative image can be passed as a positional argument. The terminal requires a 64 KB banked image; legacy 8 KB test fixtures remain available through the machine API.

## Commands

Addresses and data bytes are **hexadecimal**, with optional `$` or `0x` prefixes. Counts are **decimal**. Displayed banks are physical banks 0–3; host `:bank` choices remain 1–4.

| Command | Behavior |
| --- | --- |
| `:help` | Show command help |
| `:run` | Run continuously until stopped or a breakpoint is hit |
| `:stop` | Pause without changing machine state |
| `:continue` | Run at most 1,000,000 instructions, respecting breakpoints |
| `:step` / `:step 10` | Pause and execute one / ten opcodes; counts 1–10000 |
| `:regs` | Pause and show CPU registers, flags, bank, and cycles |
| `:status` | Show the same state without pausing a running machine |
| `:mem 0300 64` | Pause and inspect 64 bytes, with hex/ASCII output |
| `:write 0300 41 42 43` | Pause and write RAM bytes `$41,$42,$43` |
| `:pc 0400` | Pause and set PC to `$0400`; other registers/stack remain unchanged |
| `:break C000` | Add a breakpoint at `$C000` in the currently selected bank |
| `:break E100 all` | Add a breakpoint at `$E100` in every bank |
| `:break` | List breakpoints |
| `:delete C000` | Remove that address breakpoint in the current bank |
| `:delete E100 all` | Remove the all-bank breakpoint |
| `:delete all` | Remove all breakpoints |
| `:bank 1` through `:bank 4` | Set external toggles under reset into selected personality |
| `:reset` | Reset current bank |
| `:quit` | Exit emulator |

Memory reads allow 1–4096 bytes (default 64) without wrapping past `$FFFF`. Memory writes accept 1–256 bytes wholly within RAM `$0000–$7FFF`; invalid values/ranges are rejected before any write. This first debugger does not write ROM or device registers. Use firmware POKE/Woz commands for hardware accesses, or host `:bank` controls to select ROMs.

Register output shows PC, A, X, Y, SP, P, decoded `NVUBDIZC` flags, physical bank, execution state, and cycle count. A dot indicates a clear bit; U/B reflect the upstream CPU model. Cycles restart at zero on reset.

## A small debugging session

Start with `--paused`, then enter:

```text
:write 0400 A9 42 8D 00 03 E8 4C 05 04
:pc 0400
:break 0405
:run
```

This RAM program loads `$42`, stores it at `$0300`, then loops over `INX` and `JMP`. Execution stops before the first INX at `$0405`. Inspect it:

```text
:regs
:mem 0300 1
:step
:regs
:run
```

The RAM byte is `$42`; stepping increments X once. Continuing reaches the loop breakpoint again. To run freely:

```text
:delete all
:run
```

Type `:stop` or press Ctrl-C, then inspect registers. This changes no firmware or ROM bank.

For boot debugging, `:break C000` followed by `:reset` stops before the current payload's first instruction. `:break C000 all` applies to every personality. See [ROM-SWITCHING.md](ROM-SWITCHING.md) for bank numbering and software switching.

## Breakpoint and timing semantics

Breakpoints are host-side address checks, not patched BRK opcodes. They persist across bank changes and reset. A hit stops before the matching opcode executes. Resuming a hit skips that same breakpoint once so execution can move forward; a later loop visit stops again. Inspecting registers/memory does not cancel that resume behavior. Explicit stepping ignores breakpoints for its requested instruction count.

Pending IRQ entry occurs before the next opcode check. A breakpoint at an IRQ handler stops after the CPU has stacked the interrupted context and consumed seven entry cycles, but before its first handler opcode. Stepping executes one opcode plus any pending IRQ entry. CPU instruction cycles, IRQ-entry cycles, and VIA/serial advancement stay on the machine's existing execution path.

The event loop owns the machine in one thread and advances it in chunks of at most 1000 instructions before polling host input. Ctrl-C sets a stop request rather than raising an exception inside a CPU/device update. Stop takes effect at a completed instruction boundary. Synchronous multi-step commands are bounded to 10000 instructions. While paused, simulated time does not advance.

This is not wall-clock throttling or a more cycle-accurate CPU. It does not change the existing instruction-level timing limitations or add 2 MHz serial support.

## Non-destructive inspection

Debugger memory reads use `MemoryBus.peek()`. They do not clear VIA timer/control/shift flags, acknowledge IRQ, pop serial input frames, update port inputs, or advance time. Normal CPU reads retain their documented hardware side effects. A debugger view is therefore an inspection snapshot, not a simulated bus transaction.

Firmware-triggered bank resets clear the serial capture as before; the terminal tracks reset generation so the new bank's complete banner remains visible. Serial CR/LF normalization works even when output arrives across multiple execution chunks.

## Limits and validation

Input remains line-oriented; there is no raw character terminal, disassembly view, watchpoint, saved machine state, or source-level debugging yet. Breakpoints are not saved across emulator processes. BASIC firmware Ctrl-C scanning is still unimplemented: host Ctrl-C pauses the emulator instead of delivering a BASIC break character. Unsupported VIA mode errors stop execution and report the error; this does not roll back a partially attempted instruction.

Tests cover opcode stepping, break-before-write, loop resume, bank-scoped/global breakpoints, reset behavior, IRQ-handler entry, side-effect-free device inspection, validated RAM editing, and software-bank resets. Real subprocess tests cover continuous execution, `:stop`, SIGINT pause/resume, piped commands, and existing BASIC/Woz/diagnostic terminal flow.

Current schematic migration (2026-10-24): VIA1 `$B000–$B7FF`, VIA2 `$B800–$BFFF`, repeated 16-register aliases; PA0 TX/PA1 RX. Manual bank toggles plus reset replace software selection. `$E106` returns carry set; `$8020` is unpopulated expansion. See [ROM switching](ROM-SWITCHING.md). LCD mirror/dashboard support is implemented; see [LCD guide](LCD.md).
