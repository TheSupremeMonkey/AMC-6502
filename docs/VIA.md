# Classic 6522 model

`emulator/via.py` provides two independent classic 6522 models at `$B000–$B7FF` and `$B800–$BFFF`. The machine combines their active interrupt requests onto one CPU IRQ input. This is the working emulator wiring; the physical board wiring is still to be designed. Legacy single-bank 8 KB regression fixtures intentionally retain their earlier unmapped I/O behavior.

## Implemented register behavior

Offsets below are relative to either VIA's base address.

| Offset | Register | Implemented behavior |
| --- | --- | --- |
| `$0` | ORB/IRB | Port B output latch/input read; acknowledges CB1 and dependent CB2 flags |
| `$1` | ORA/IRA | Port A output latch/input read; acknowledges CA1 and dependent CA2 flags |
| `$2–$3` | DDRB/DDRA | Per-bit output/input selection |
| `$4` | T1 counter low | Read counter and acknowledge T1; write low latch |
| `$5` | T1 counter high | Read counter; write high latch and load/start T1, acknowledge T1 |
| `$6–$7` | T1 latch low/high | Read/write latch without restarting counter; high write acknowledges T1 |
| `$8` | T2 counter low | Read counter and acknowledge T2; write low latch |
| `$9` | T2 counter high | Read counter; write high counter and load/start T2, acknowledge T2 |
| `$A` | Shift register | Storage and flag acknowledgement only; shift engine not implemented |
| `$B` | ACR | Input latching, timer modes, and PB7 timer control; active shift modes rejected |
| `$C` | PCR | Control-input edge polarity, independent CA2/CB2 flags, fixed low/high outputs; handshake/pulse output modes rejected |
| `$D` | IFR | Latched source flags; bit 7 summarizes enabled pending sources; write-one-to-clear bits 0–6 |
| `$E` | IER | Bit 7 selects set/clear of supplied enable bits; reads always return bit 7 set |
| `$F` | ORA/IRA alias | Same data path as `$1`, without handshake acknowledgement |

Pins are deterministically high when undriven in this model. `set_port_a()`, `set_port_b()`, and `set_control()` provide external stimulus; `pins_a`/`pins_b` expose the combined output/input values. VIA #1 PA1 is supplied by the serial peer and PA0 drives serial TX. Other input bits remain independently controllable.

Port latching samples input A/B on the selected CA1/CB1 edge when ACR latching is enabled. PCR selects active control edges and whether CA2/CB2 input flags clear with port access. Fixed CA2/CB2 output levels are exposed in the model's `lines` dictionary. There is no timed output handshake sequencer.

## Timers

Timer 1 supports one-shot and free-running modes. Loading its high counter starts it and arms its interrupt. One-shot expiry sets IFR6 once; the counter continues wrapping without generating further interrupts until reloaded. Free-running expiry reloads from the latch and can generate repeated interrupts. Updating the latch changes a future reload, not the countdown already in progress.

PB7 starts low on a T1 load and goes high on one-shot expiry, or toggles at free-running expiry. The modeled timer output requires both ACR7 and DDRB7; otherwise normal port direction/latch behavior applies. This follows the cited Rockwell description, rather than assuming every modern or vendor-specific variant is identical.

Timer 2 supports timed one-shot operation and PB6 falling-edge pulse counting. It continues counting after expiry but only flags its first underflow until reloaded. External PB6 changes and output/direction changes that create falling pin edges are counted in pulse mode. Timed cycles do not decrement T2 in pulse mode.

At the standalone device API, a timed load of N expires after N+2 integer PHI2 cycles. Free-running T1 uses N+2-cycle periods. The integer model includes a load/reload delay and rounds the datasheet's half-cycle IRQ timing to a whole cycle. Pulse-mode T2 underflows after N+1 falling edges. Set timer modes before loading the counters; detailed mode-change races are not validated.

## Interrupt and reset behavior

Events set source flags even when IER masks the source. Enabling an already-pending source asserts IRQ immediately. Disabling it deasserts IRQ without clearing the event. Each VIA computes IFR7 from `(IFR & IER & $7F) != 0`; writing IFR7 alone does not clear all flags. Reading timer low counters or writing their high counters acknowledges the corresponding timer source.

The machine checks the combined level IRQ at instruction boundaries. When the CPU's I flag is clear, Py65 enters through `$FFFE–$FFFF`; its seven IRQ-entry cycles advance both VIAs and the serial peer before the first handler instruction. RTI can expose an unacknowledged level interrupt again. NMOS IRQ entry preserves decimal mode; no CMOS IRQ behavior is assumed.

Reset clears enables/flags, ports/directions, timer-running state, control modes, and input-latch state. Timer counters use deterministic `$FFFF` defaults and latches use zero; this does not assert physical power-on counter contents. Both VIA models reset on bank-button reset; RAM and the bank selector remain intact.

## Verification

`make test` assembles `firmware/via-irq.s` into a 16 KB diagnostic fixture, replicated into all four banks for testing. The diagnostic:

1. Starts VIA #1 T1 while SEI masks CPU interrupts and records pending IFR `$C0`.
2. Executes CLI, receives the IRQ, acknowledges T1, and increments a RAM counter.
3. Starts VIA #2 T2, receives/acknowledges its IRQ, and increments a second counter.
4. Writes pass marker `$42` to `$0203` and loops.

Focused tests additionally cover repeated free-running interrupts through the real handler, both-source IRQ aggregation, uncleared IRQ re-entry after RTI, seven-cycle IRQ accounting, preserved NMOS decimal mode, timer boundaries, masking/acknowledgement, latch updates, PB7 output, PB6 pulse counting, control-edge flags, port latching, and reset. Existing BASIC/Woz serial and bank-switching tests remain regression checks. The main image also runs [bank 3 diagnostics](DIAGNOSTICS.md), with shared-kernel IRQ dispatch and fault-injection coverage.

## Fidelity limits

This is instruction-level firmware emulation. Register accesses occur at the instruction's starting cycle and device time advances at its end; timer expiry relative to a register access can therefore differ by an instruction's bus-access offset. Exact PHI2 edges, read/modify/write dummy bus accesses, IRQ polling delays around CLI/SEI/PLP, and simultaneous acknowledge/expiry races are not modeled. It is not suitable for proving physical timing or cycle-sensitive interrupt latency.

Shift-register modes and CA2/CB2 timed handshake/pulse outputs raise `NotImplementedError` when enabled rather than silently pretending to work. Full classic-chip shift quirks, output handshake sequencing, and exhaustive input-latch timing remain future work. Bit-bang serial still uses fixed 1 MHz delays; this change does not add 2 MHz serial support or LCD functionality.

## References

- [Rockwell R6522 datasheet scan](https://www.princeton.edu/~mae412/HANDOUTS/Datasheets/6522.pdf): register map, timer and interrupt operation.
- [Rockwell 1981 data book](https://www.bitsavers.org/components/rockwell/_dataBooks/1981_Rockwell_Electronic_Devices_Division_Data_Book.pdf): R6522/R6522A timer timing diagrams, PB7 qualification, and one-shot behavior.

The implementation and tests state their integer-cycle policy explicitly; these references do not imply full chip-level validation.

Current schematic migration (2026-10-24): VIA1 `$B000–$B7FF`, VIA2 `$B800–$BFFF`, repeated 16-register aliases; PA0 TX/PA1 RX. Manual bank toggles plus reset replace software selection. `$E106` returns carry set; `$8020` is unpopulated expansion. See [ROM switching](ROM-SWITCHING.md). LCD mirror/dashboard support is implemented; see [LCD guide](LCD.md).
