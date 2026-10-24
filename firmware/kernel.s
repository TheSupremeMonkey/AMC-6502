.setcpu "6502"
.include "fw.inc"
; Provisional shared ABI. UART: 9600-ish 8N1 at 1 MHz (104-cycle bits).
VIA_ORA = VIA1_ORA
DDRA = VIA1_DDRA
TXBYTE = FW_TX_SCRATCH
RXBYTE = FW_RX_SCRATCH
IRQ_VECTOR = FW_IRQ_VECTOR
BANK_INFO = FW_BANK_INFO
BANK_INFO_SIZE = FW_BANK_INFO_SIZE
.segment "KERNEL"
    jmp reset
.segment "ABI"
    jmp cout                   ; $E100
    jmp cin                    ; $E103
    jmp select_bank            ; $E106: retired, returns carry set
    jmp puts                   ; $E109: A/Y string pointer, bounded 256-byte scan
    jmp hex8                   ; $E10C: A byte -> two hex digits
    jmp hex16                  ; $E10F: A/Y low/high word -> four hex digits
    jmp readline               ; $E112: A maximum length -> fixed line buffer
    jmp cin_poll               ; $E115: C=1 character in A, C=0 no input
    jmp version                ; $E118: A/X/Y major/minor/patch
    jmp bank_get               ; $E11B: A current physical bank 0..3
    jmp crlf                   ; $E11E: print CR/LF
    jmp loader                 ; $E121: checksummed Intel HEX upload
    jmp lcd_mode               ; $E124: A=0 off,1 mirror,2 dashboard
    jmp lcd_clear              ; $E127
    jmp lcd_status             ; $E12A: A/Y dashboard status string
.segment "DRIVERS"
reset:
    sei
    cld
    ldx #$ff
    txs
    lda #<default_irq
    sta IRQ_VECTOR
    lda #>default_irq
    sta IRQ_VECTOR+1
    lda #1
    sta FW_PORTA_SHADOW
    sta VIA_ORA
    sta DDRA                   ; PA0 TX output, PA1 RX input
    lda #0
    sta FW_SKIP_LF
    sta LCD_ACTIVE
    sta LCD_ERROR
    lda LCD_COOKIE
    cmp #$a5
    bne @default_lcd
    lda LCD_COOKIE+1
    cmp #$5a
    bne @default_lcd
    lda FW_LCD_REQUEST
    cmp #3
    bcc @lcd_configured
@default_lcd:
    lda #0
    sta FW_LCD_REQUEST
@lcd_configured:
    lda #$a5
    sta LCD_COOKIE
    lda #$5a
    sta LCD_COOKIE+1
    jsr lcd_poll_preserve
    jsr boot_banner
    jmp $c000                  ; identical entry in each payload
irq:
    jmp (IRQ_VECTOR)
default_irq:
    rti
; 83 cycles including JSR/RTS. No page-crossing branch penalty.
delay:
    ldx #14
@loop:
    dex
    bne @loop
    rts
first_delay:
    ldx #21                  ; allow polling detection latency and PA1 shift cycles
@loop:
    dex
    bne @loop
    rts
serial_cout:
    php
    cld
    pha
    and #$7f                  ; historical BASIC marks string ends with bit 7
    sta TXBYTE
    txa
    pha
    tya
    pha
    lda FW_PORTA_SHADOW
    and #$fe
    sta FW_PORTA_SHADOW
    sta VIA_ORA                    ; start bit, preserve other output latches
    jsr delay
    ldy #8
@bit:
    lsr TXBYTE
    lda FW_PORTA_SHADOW
    and #$fe
    adc #0
    sta FW_PORTA_SHADOW
    sta VIA_ORA
    jsr tx_delay
    dey
    bne @bit
    lda FW_PORTA_SHADOW
    ora #1
    sta FW_PORTA_SHADOW
    sta VIA_ORA                    ; stop bit
    jsr delay
    pla
    tay
    pla
    tax
    pla
    plp
    rts
tx_delay:
    ldx #13
@loop:
    dex
    bne @loop
    rts
cout:
    php
    pha
    txa
    pha
    tya
    pha
    cld
    jsr lcd_poll
    lda LCD_ACTIVE
    cmp #1
    bne @done
    tsx
    lda $0103,x
    jsr lcd_console
@done:
    pla
    tay
    pla
    tax
    pla
    plp
    jmp serial_cout            ; echo only after LCD work, preserving upload pacing
cin:
    jsr lcd_poll_preserve
    txa
    pha
    tya
    pha
@wait:
    lda FW_LCD_REQUEST
    cmp LCD_ACTIVE
    beq @sample
    jsr lcd_poll_preserve
@sample:
    lda VIA_ORA
    and #2
    bne @wait
    jsr receive_byte
    sec
    jmp restore_rx
cin_poll:
    lda VIA_ORA
    and #2
    beq @receive
    lda FW_LCD_REQUEST
    cmp LCD_ACTIVE
    beq @empty
    jsr lcd_poll_preserve
    jmp @empty
@receive:
    txa
    pha
    tya
    pha
    jsr receive_byte
    sec
    jmp restore_rx
@empty:
    lda #0
    clc
    rts
receive_byte:
    jsr first_delay
    ldy #8
@bit:
    lda VIA_ORA
    lsr a
    lsr a
    ror RXBYTE
    jsr delay
    nop
    nop
    dey
    bne @bit
    rts
restore_rx:
    pla
    tay
    pla
    tax
    lda RXBYTE
    and #$7f
    rts
; Keep banner code/data away from timing-sensitive console driver loops.
.segment "BOOT"
select_bank:
    sec                        ; no software bank hardware exists
    rts
boot_banner:
    lda #<boot_text
    ldy #>boot_text
    jsr puts
    ldx #0
@bank:
    lda BANK_INFO,x
    beq @end_bank
    jsr cout
    inx
    cpx #BANK_INFO_SIZE
    bne @bank
@end_bank:
    lda #13
    jsr cout
    lda #10
    jsr cout
    rts
boot_text:
    .byte 13,10
    .byte "   /\        A M C - 6 5 0 2",13,10
    .byte "  /  \       ASTROMONKEY MICRO COMPUTER",13,10
    .byte "  |==|       SYSTEM ROM 0.1",13,10
    .byte " /|  |\      32K RAM / 4 ROM BANKS",13,10
    .byte "  /||\",13,10
    .byte "========== READY FOR LAUNCH ==========",13,10,13,10,0
    .assert *-boot_text <= 256, error, "Boot text exceeds indexed print range"
.segment "SERVICES"
; A/Y = low/high pointer. Preserve A/X/Y; C=0 terminated, C=1 after 256 bytes.
puts:
    sta FW_STRPTR
    sty FW_STRPTR+1
    pha
    txa
    pha
    tya
    pha
    ldy #0
@char:
    lda (FW_STRPTR),y
    beq @done
    jsr cout
    iny
    bne @char
    sec
    bcs @restore
@done:
    clc
@restore:
    pla
    tay
    pla
    tax
    pla
    rts
hex8:
    php
    cld
    pha
    lsr a
    lsr a
    lsr a
    lsr a
    jsr hex_digit
    pla
    pha
    and #$0f
    jsr hex_digit
    pla
    plp
    rts
hex_digit:
    cmp #10
    bcc @digit
    clc
    adc #7
@digit:
    clc
    adc #'0'
    jmp cout
hex16:
    php
    pha
    tya
    jsr hex8
    pla
    jsr hex8
    plp
    rts
crlf:
    pha
    lda #13
    jsr cout
    lda #10
    jsr cout
    pla
    rts
version:
    lda #FW_VERSION_MAJOR
    ldx #FW_VERSION_MINOR
    ldy #FW_VERSION_PATCH
    rts
bank_get:
    lda BANK_INFO+5            ; "BANK n:" metadata follows physical ROM selection
    sec
    sbc #'0'
    rts
; Blocking line editor: A=1..111. C=0,A=0,X=length; invalid C=1,A=1,X=0.
; Y preserved. Buffer is always NUL-terminated. CR/LF finish; BS/DEL erase.
readline:
    cmp #1
    bcc @invalid
    cmp #FW_LINE_MAX+1
    bcs @invalid
    sta FW_LINE_LIMIT
    tya
    pha
    lda #0
    sta FW_LINE_LENGTH
    sta FW_LINEBUF
    jmp line_next
@invalid:
    lda #1
    ldx #0
    sec
    rts
line_next:
    jsr cin
    ldx FW_SKIP_LF
    beq @process
    ldx #0
    stx FW_SKIP_LF
    cmp #10
    beq line_next
@process:
    cmp #13
    beq line_cr
    cmp #10
    beq line_done
    cmp #8
    beq line_erase
    cmp #127
    beq line_erase
    cmp #32
    bcc line_next
    ldx FW_LINE_LENGTH
    cpx FW_LINE_LIMIT
    bcs line_full
    sta FW_LINEBUF,x
    tay
    inx
    stx FW_LINE_LENGTH
    lda #0
    sta FW_LINEBUF,x
    tya
    jsr cout
    jmp line_next
line_full:
    lda #7                    ; BEL: capacity reached; input is not stored
    jsr cout
    jmp line_next
line_erase:
    ldx FW_LINE_LENGTH
    beq line_next
    dex
    stx FW_LINE_LENGTH
    lda #0
    sta FW_LINEBUF,x
    lda #8
    jsr cout
    lda #' '
    jsr cout
    lda #8
    jsr cout
    jmp line_next
line_cr:
    lda #1
    sta FW_SKIP_LF
line_done:
    jsr crlf
    pla
    tay
    ldx FW_LINE_LENGTH
    lda #0
    clc
    rts
.include "loader.inc"
.include "lcd.inc"
.segment "BANK_INFO"
    .res BANK_INFO_SIZE, 0      ; builder fills this sole bank-specific upper-ROM field
.segment "CPU_VECTORS"
    .word default_irq, reset, irq
