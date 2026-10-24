# Shared firmware API 0.4.0

Implemented services for classic NMOS 6502 firmware at the 1 MHz baseline. Include [fw.inc](../firmware/include/fw.inc) in assembly sources with ca65's `-I firmware/include` option. Symbols, vector addresses, and workspace constants are defined there.

The original `$E100`, `$E103`, and `$E106` entries stay fixed. New services append three-byte JMP entries; callers must use the public table rather than internal routine addresses. All code/table bytes are mirrored across banks; only the existing bank description field differs.

## Calling conventions

Use JSR for returning services. The retired bank-selection slot returns carry set for all inputs. A/Y pointers and words use **A = low byte, Y = high byte**. Unless specified otherwise, flags are unspecified; D/I are preserved by returning services. Serial helpers are non-reentrant and must be called with IRQ disabled, or with an application policy that prevents interrupts from disturbing their timing/scratch. Do not call them from IRQ/NMI while another serial/helper call is active.

| Address | Symbol | Input | Result and preservation |
| --- | --- | --- | --- |
| `$E100` | `FW_COUT` | A = character | Output low 7 bits; A/X/Y preserved |
| `$E103` | `FW_CIN` | None | Blocking input; A = 7-bit character, C=1; X/Y preserved |
| `$E106` | `FW_BANK_SELECT` (retired) | Any | C=1; no switch/reset; returns |
| `$E109` | `FW_PUTS` | A/Y = NUL-terminated string pointer | A/X/Y preserved; C=0 found NUL, C=1 scan limit reached |
| `$E10C` | `FW_HEX8` | A = byte | Two uppercase hex digits; A/X/Y and P preserved |
| `$E10F` | `FW_HEX16` | A/Y = low/high word | Four uppercase hex digits, high byte first; A/X/Y and P preserved |
| `$E112` | `FW_READLINE` | A = maximum characters, 1–111 | C=0, A=0, X=length; Y preserved; text at `FW_LINEBUF` |
| `$E115` | `FW_CIN_POLL` | None | Idle: C=0,A=0. Received: C=1,A=character, including NUL. X/Y preserved |
| `$E118` | `FW_VERSION` | None | A=major, X=minor, Y=patch; currently 0,4,0 |
| `$E11B` | `FW_BANK_GET` | None | A=current bank 0–3 from ROM metadata; X/Y preserved |
| `$E11E` | `FW_CRLF` | None | Output CR/LF; A/X/Y preserved |
| `$E121` | `FW_LOAD` | None | Intel HEX loader; EOF A=0,C=0; ESC A=1,C=1; X/Y clobbered, D/I preserved |
| `$E124` | `FW_LCD_MODE` | A=0 off,1 mirror,2 dashboard | C=0 success, C=1 invalid/NACK; A clobbered, X/Y and D/I preserved |
| `$E127` | `FW_LCD_CLEAR` | None | C=0 success, C=1 off/fault; A/X/Y and D/I preserved |
| `$E12A` | `FW_LCD_STATUS` | A/Y string pointer | Dashboard last row, bounded 20 characters; C=1 off/fault; A/X/Y and D/I preserved |

HEX routines clear decimal mode internally and restore the caller's status flags with PHP/PLP afterward (B/U follow the CPU model), so formatting also works when the caller has D set. No other arithmetic-formatting services are implied.

PUTS examines at most 256 bytes: at most 255 non-NUL characters followed by NUL is a normal successful string. If all 256 bytes are nonzero, it prints them and returns C=1. Page crossings are supported. Supply a readable RAM/ROM source that does not overlap scratch used by the service; the completed line buffer is a valid source. This routine does not validate arbitrary I/O pointers or prevent 16-bit address wrap for an invalid source.

## Edited line input

`FW_READLINE` stores a NUL-terminated string at `$0280`. CR or LF finishes the line and echoes CR/LF. BS (`$08`) and DEL (`$7F`) erase the last character using BS/space/BS; erase on an empty line is ignored. Other controls are ignored. Printable ASCII is echoed as it is stored.

Maximum length is supplied by the caller, from 1 to 111. Characters beyond that limit are ignored with BEL; backspace can free space again. The buffer remains terminated. A line of length zero is valid. Invalid limits return **C=1,A=1,X=0**, preserve Y, and do not modify the buffer or read input.

A CR sets a flag to ignore one leading LF on the next edited-input call, preventing CR/LF from creating an extra empty line. Raw CIN/POLL do not perform newline coalescing; applications mixing raw and edited input must account for that state. Input editing is blocking; host Ctrl-C pauses the emulator, not a firmware cancellation result.

## Polling is not background buffering

The current driver is software serial. POLL returns immediately if the RX pin is high. If it sees a low start bit, it receives the rest of that character synchronously, taking roughly one millisecond at 1 MHz/approximately 9600 baud. This is **idle-nonblocking polling**, not a hardware UART or an asynchronous queue.

For reliable use, enter a tight polling loop before the incoming start bit; a simple `JSR FW_CIN_POLL` / `BCC` loop samples often enough in the tested model. Sporadic calls during a computation can miss the start or mistake a low data bit for one. No reliable receive service while arbitrary foreground code runs, framing-error recovery, or clock-speed switching is implemented. Blocking CIN uses the same receiver, with a faster dedicated idle wait. Output is ASCII/7-bit; it is not a binary-transparent transfer protocol.

## RAM ownership

| RAM | Owner / use |
| --- | --- |
| `$00F0–$00F1` | Kernel transient string pointer; applications must not allocate it |
| `$00F2–$00F3` | LCD status-string pointer |
| `$0200–$027F` | Personality-owned; Woz input buffer and test-fixture mailboxes use this area |
| `$0280–$02EF` | Kernel line buffer: 111 characters plus NUL |
| `$02F0–$02F1` | Kernel serial transmit/receive scratch |
| `$02F2–$02F3` | Kernel/application IRQ hook, initialized by shared reset |
| `$02F4–$02F8` | Personality-owned; diagnostics scratch, not kernel allocations |
| `$02F9–$02FB` | Kernel line limit, length, and pending-LF flag |
| `$02FC` | Shared Port A output-latch shadow; peripheral output writers must maintain it |
| `$02FD` | LCD mode request mailbox |
| `$02FE–$02FF` | Unallocated |
| `$0300–$7F7F` | User RAM managed by the active personality |
| `$7F80–$7FFF` | LCD buffer, scratch and warm-reset marker |

The stack at `$0100–$01FF` remains CPU stack space and must have room for nested helper calls. No permanent kernel buffers occupy BASIC's user allocation region. BASIC's selected configuration already starts user RAM at `$0300`; build-time assertions check its zero-page end stays below `$F0` and its user RAM starts at or above `$0300`. Woz's buffer ends at `$027F`, before the new line buffer. The diagnostic scan starts at `$0300`, excluding kernel scratch.

Applications can read the completed line buffer but should not allocate it as persistent private storage. Service scratch is volatile. Reset does not clear all retained RAM; line input initializes its own length/buffer, and reset clears the pending-LF state. The shared IRQ hook contract remains unchanged. IRQ resource scheduling and future keyboard/LCD/tick ownership are still separate work.

## Example

```asm
.setcpu "6502"
.include "fw.inc"
.segment "CODE"

    sei                         ; current software serial timing requirement
    lda #<greeting
    ldy #>greeting
    jsr FW_PUTS
    lda #$ab
    jsr FW_HEX8                 ; AB
    jsr FW_CRLF

    lda #40
    jsr FW_READLINE
    bcs input_error
    lda #<FW_LINEBUF
    ldy #>FW_LINEBUF
    jsr FW_PUTS
    jsr FW_CRLF
    jsr FW_BANK_GET             ; A = physical bank, 0..3
    jsr FW_HEX8
    jsr FW_CRLF
idle:
    jmp idle
input_error:
    lda #'?'
    jsr FW_COUT
    jmp idle

greeting: .byte "VALUE: ",0
```

BASIC and Woz retain their own input editors for now. Diagnostics uses the shared PUTS service instead of a private string driver. These helpers provide console/loader and LCD support; SAVE, keyboard and operating profiles remain pending.

## Build and validation

```sh
make test-api
make test
```

`make test-api` assembles `firmware/abi-test.s` and runs the focused API tests with the real shared kernel. The test payload is replicated into a temporary in-memory four-bank image; production bank 1 remains reserved.

Coverage includes formatted output, register/decimal-mode preservation, firmware/bank queries in all four banks, page-crossing and unterminated strings, BS/DEL editing, capacity/terminator bounds, invalid limits, CR/LF handling, idle versus NUL polling, and receive start-bit phases. All input/output runs through actual firmware and the modeled VIA/serial pins, without CPU-PC console traps. Full tests retain BASIC/Woz, bank/reset, diagnostics/fault injection, and debugger regression checks.

The generated kernel map reports actual segment use and link-time bounds keep the code below reserved metadata/vectors. New helpers are in the SERVICES section beginning at `$E800`; clients must not call that internal location directly.

## Serial program transfer

[Serial loader](SERIAL-LOADER.md) defines the protocol, workspace, sender, and protection rules. FW_LOAD reuses/clobbers the complete line buffer and PUTS pointer, with no additional reserved RAM.

Port A output writers must maintain `FW_PORTA_SHADOW` at `$02FC` and preserve unrelated DDRA bits. The serial driver owns PA0 only; PA1 is RX. PA2–PA7 stay input/unclaimed at boot. LCD/I2C claims PA2/PA3 only when enabled; SD remains deferred.

LCD service slots `$E124` MODE, `$E127` CLEAR and `$E12A` STATUS append to the table. Full contracts and workspace are in [LCD.md](LCD.md). Mode 1 mirrors COUT; mode 2 keeps an independent application dashboard.
