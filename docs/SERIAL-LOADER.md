# Serial RAM loader

Shared firmware API 0.4.0 includes `FW_LOAD` at `$E121`. Diagnostics (physical bank 3, host `:bank 4`) accepts `L` to enter the loader. It transfers data into RAM without executing it. BASIC program save/restore and downloads remain future work.

## Try it

```
make rom
.venv/bin/python scripts/send_hex.py --emulator examples/ram-test.hex
```

The sender boots a fresh emulator, selects diagnostics, enters `L`, and transfers through actual VIA serial pins and assembled firmware. This command's emulator is temporary; RAM disappears when it exits. Integration tests inspect uploaded bytes and explicitly execute the example.

For an interactive persistent machine, run `make run`, select `:bank 4`, enter `L`, then paste one HEX record per console line, waiting for `OK` between records. Finish with EOF. The terminal adds CR and its existing paced input is sufficient for these records. Example [ram-test.hex](../examples/ram-test.hex) loads classic instructions at `$0300`: `LDA #$42; STA $0400; JMP $0305`. After `DONE`, use `:pc 0300`, `:step 2`, and `:mem 0400 1` to see `42`. Alternatively select Woz (`:bank 3`) and enter `0300R`; Woz initialization leaves this example's RAM intact. Firmware initialization in other personalities may overwrite an uploaded program.

A stdlib-only POSIX serial transport is also provided:

```
.venv/bin/python scripts/send_hex.py --port /dev/ttyUSB0 examples/ram-test.hex
```

Leave the target waiting at the diagnostics menu, close the terminal connection, then start the sender with exclusive access to the device. It sends `L` automatically and expects `HEX READY` within ten seconds. Adapter configuration is 9600 baud, 8N1, no hardware flow control; prior terminal settings are restored on exit. Physical hardware timing is unverified. The firmware remains timed for the 1 MHz baseline.

## Wire protocol

Intel HEX ASCII records use `:llaaaatt[dd...]cc`, uppercase or lowercase hex. `ll` is byte count, `aaaa` is a 16-bit address, `tt` is type, and `cc` makes the byte sum modulo 256 zero. Supported types are 00 (0–16 data bytes) and exactly `:00000001FF` (EOF). Extended addresses and execution/start records are rejected. CR terminates a record; send **CR only**, without LF. Spaces and edited/backspaced input are unsupported.

On entry firmware sends `HEX READY\r\n`. Each non-CR character is echoed; wait for this echo before sending the next character. After CR it sends `\r\n`, then `OK\r\n`, `ERR\r\n`, or `DONE\r\n`. Wait for that response before another record. The sender stops on any unexpected response, including ERR. Serial receives have a ten-second host timeout; emulator receives have bounded instruction budgets. Firmware waits indefinitely for input; ESC cancels at any point during record reception and sends `ABORT\r\n`.

Records are limited to 43 characters. Excess input is discarded through CR and the entire record is rejected. Length, digits, checksum, type, and the complete address range are checked **before any destination write**. Only `$0300–$7F7F` is writable, protecting zero page, stack, kernel/monitor workspace, I/O, and ROM. A record ending exactly at `$7F80` is allowed; crossing it or wrapping addresses is rejected. Rejected records change no destination bytes. Earlier accepted records remain; the transfer is atomic per record, not per file. Overlapping accepted records overwrite earlier data.

After ERR firmware stays in the loader and accepts a corrected record or ESC. EOF/ESC returns to its caller; diagnostics redisplays its menu. Host preflight validates the complete file before opening a connection. Checksums detect ordinary transfer errors; this is a trusted development interface.

## Assembly contract and verification

`JSR FW_LOAD` requires initialized serial hardware and writable stack. No arguments. It preserves D/I, masks IRQ and clears decimal mode while active, and returns A=0,C=0 on EOF or A=1,C=1 on ESC; X/Y and other flags are unspecified. It is non-reentrant and clobbers the entire shared line buffer `$0280–$02EF` and PUTS pointer `$F0–$F1`. No new persistent RAM reservation is needed. NMI must not disturb serial timing or shared scratch.

`tests/test_loader.py` covers valid transfer and explicit execution, exact RAM boundaries, checksum corruption, malformed digits/length, unsupported records, protected/crossing/wrapping addresses, overflow, recovery, abort/menu return, and sender preflight through actual firmware and modeled serial pins. Run `make test-loader` for focused checks or `make test` for all regressions. Baud/framing error detection, retries, whole-file rollback, download, and automatic launch remain unimplemented.

LCD reserves `$7F80–$7FFF`; this area is excluded from user uploads and restoring diagnostics. See [LCD.md](LCD.md).
