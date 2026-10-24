; LCD2004 + PCF8574. All code is classic NMOS 6502.
; Configurable backpack wiring: P0 RS, P1 RW, P2 E, P3 BL, P4..7 data.
LCD_ADDRESS = $27             ; TODO: verify actual backpack address before hardware bring-up
LCD_BUFFER = $7f80             ; 80-byte scrolling console image
LCD_ROW = $7fd0
LCD_COL = $7fd1
LCD_BYTE = $7fd2
LCD_RS = $7fd3
LCD_NIBBLE = $7fd4
I2C_BYTE = $7fd5
I2C_COUNT = $7fd6
LCD_ERROR = $7fd7
LCD_ACTIVE = $7fd8
LCD_TARGET = $7fd9
LCD_CR = $7fda
LCD_INDEX = $7fdb
LCD_LINE_COUNT = $7fdc
LCD_COOKIE = $7ffe             ; warm-reset configuration marker (not nonvolatile)
LCD_PTR = $f2                  ; $F2/$F3 kernel ZP
.segment "LCD"
lcd_poll_preserve:
    php
    pha
    txa
    pha
    tya
    pha
    cld
    jsr lcd_poll
    pla
    tay
    pla
    tax
    pla
    plp
    rts
lcd_poll:
    lda FW_LCD_REQUEST
    cmp #3
    bcc @valid_request
    lda LCD_ACTIVE
    sta FW_LCD_REQUEST
    rts
@valid_request:
    cmp LCD_ACTIVE
    beq @done
    jmp lcd_mode
@done:
    rts

; A=0 off,1 mirror,2 dashboard. Preserve X/Y,D/I. C=1 invalid/NACK.
lcd_mode:
    cmp #3
    bcc @valid
    sec
    rts
@valid:
    php
    sei
    cld
    sta LCD_TARGET
    sta FW_LCD_REQUEST
    txa
    pha
    tya
    pha
    lda #0
    sta LCD_ERROR
    lda LCD_TARGET
    bne @enable
    lda LCD_ACTIVE
    beq @off
    lda #8
    jsr lcd_command
    lda #0
    jsr i2c_port              ; backlight off
@off:
    lda #0
    sta LCD_ACTIVE
    lda DDRA
    and #$f3
    sta DDRA
    jmp lcd_mode_done
@enable:
    lda FW_PORTA_SHADOW
    and #$f3                 ; output low or release as input, never drive I2C high
    sta FW_PORTA_SHADOW
    sta VIA1_ORA_NH               ; no handshake acknowledgement
    jsr i2c_stop
    ldy #40
    jsr lcd_wait_ms
    lda #$30
    jsr lcd_init_nibble
    ldy #5
    jsr lcd_wait_ms
    lda #$30
    jsr lcd_init_nibble
    ldy #1
    jsr lcd_wait_ms
    lda #$30
    jsr lcd_init_nibble
    ldy #1
    jsr lcd_wait_ms
    lda #$20
    jsr lcd_init_nibble
    lda #$28
    jsr lcd_command
    lda #$0c
    jsr lcd_command
    lda #6
    jsr lcd_command
    jsr lcd_clear_internal
    lda LCD_ERROR
    bne @failed
    lda LCD_TARGET
    sta LCD_ACTIVE
    cmp #2
    bne lcd_mode_done
    jsr lcd_dashboard
    jmp lcd_mode_done
@failed:
    lda #0
    sta LCD_ACTIVE
    sta FW_LCD_REQUEST       ; no endless retry on a missing display
lcd_mode_done:
    pla
    tay
    pla
    tax
    plp
    lda LCD_ERROR
    beq @ok
    sec
    rts
@ok:
    clc
    rts

lcd_init_nibble:
    pha
    lda #0
    sta LCD_RS
    pla
    jmp lcd_nibble

; Millisecond wait at fixed 1 MHz; greater than 1 ms per iteration.
lcd_wait_ms:
    ldx #200
@inner:
    dex
    bne @inner
    dey
    bne lcd_wait_ms
    rts

; Each expander byte is its own addressed I2C write, with ACK checks.
i2c_port:
    pha
    lda LCD_ERROR
    beq @send
    pla
    rts
@send:
    jsr i2c_start
    lda #LCD_ADDRESS*2
    jsr i2c_send
    pla
    jsr i2c_send
    jmp i2c_stop

i2c_start:
    lda DDRA
    and #$f3
    sta DDRA                 ; released SDA/SCL
    ora #4
    sta DDRA                 ; SDA falls with SCL high
    ora #8
    sta DDRA
    rts
i2c_stop:
    lda DDRA
    ora #$0c
    sta DDRA
    and #$f7
    sta DDRA                 ; SCL rises, SDA low
    and #$fb
    sta DDRA                 ; SDA rises with SCL high
    rts
i2c_send:
    sta I2C_BYTE
    lda #8
    sta I2C_COUNT
@bit:
    asl I2C_BYTE
    lda DDRA
    ora #4
    bcc @data
    and #$fb
@data:
    sta DDRA
    and #$f7
    sta DDRA                 ; sample data while SCL high
    ora #8
    sta DDRA
    dec I2C_COUNT
    bne @bit
    and #$fb
    sta DDRA                 ; release SDA for ACK
    and #$f7
    sta DDRA
    lda VIA1_ORA_NH
    and #4
    beq @ack
    lda #1
    sta LCD_ERROR
    lda #0
    sta LCD_ACTIVE
    sta FW_LCD_REQUEST
@ack:
    lda DDRA
    ora #8
    sta DDRA
    rts
lcd_nibble:
    and #$f0
    ora LCD_RS
    ora #8                   ; backlight on, RW low
    sta LCD_NIBBLE
    jsr i2c_port
    lda LCD_NIBBLE
    ora #4
    jsr i2c_port
    lda LCD_NIBBLE
    jmp i2c_port
lcd_command:
    pha
    lda #0
    sta LCD_RS
    pla
    jsr lcd_byte
    rts
lcd_data:
    pha
    lda #1
    sta LCD_RS
    pla
lcd_byte:
    sta LCD_BYTE
    jsr lcd_nibble
    lda LCD_BYTE
    asl a
    asl a
    asl a
    asl a
    jsr lcd_nibble
    ; Bus transfers exceed normal HD44780 instruction delay; still wait 2 ms
    ; after clear/home. Fixed waits, no busy-flag reads.
    lda LCD_RS
    bne @done
    lda LCD_BYTE
    cmp #3
    bcs @done
    ldy #2
    jsr lcd_wait_ms
@done:
    rts

lcd_clear_internal:
    lda #0
    sta LCD_ROW
    sta LCD_COL
    sta LCD_CR
    ldx #79
    lda #' '
@fill:
    sta LCD_BUFFER,x
    dex
    bpl @fill
    lda #1
    jmp lcd_command

; Public clear: preserve A/X/Y and D/I; C=1 when off or faulted.
lcd_clear:
    php
    sei
    cld
    pha
    txa
    pha
    tya
    pha
    lda LCD_ACTIVE
    beq lcd_public_off
    jsr lcd_clear_internal
    jmp lcd_public_done

; A/Y points to a dashboard status string; truncate/pad to 20 characters.
lcd_status:
    sta LCD_PTR
    sty LCD_PTR+1
    php
    sei
    cld
    pha
    txa
    pha
    tya
    pha
    lda LCD_ACTIVE
    cmp #2
    bne lcd_public_off
    lda #$d4
    jsr lcd_command
    lda #0
    sta LCD_LINE_COUNT
@char:
    ldy LCD_LINE_COUNT
    lda (LCD_PTR),y
    cmp #32
    bcc @pad
    cmp #127
    bcs @pad
    jsr lcd_data
    inc LCD_LINE_COUNT
    lda LCD_LINE_COUNT
    cmp #20
    bne @char
    jmp lcd_public_done
@pad:
    lda #' '
    jsr lcd_data
    inc LCD_LINE_COUNT
    lda LCD_LINE_COUNT
    cmp #20
    bne @pad
    jmp lcd_public_done
lcd_public_off:
    pla
    tay
    pla
    tax
    pla
    plp
    sec
    rts
lcd_public_done:
    lda LCD_ERROR
    bne lcd_public_off
    pla
    tay
    pla
    tax
    pla
    plp
    clc
    rts

lcd_dashboard:
    lda #$80
    jsr lcd_command
    ldx #0
@title:
    lda lcd_title,x
    jsr lcd_data
    inx
    cpx #20
    bne @title
    lda #$c0
    jsr lcd_command
    ldx #0
@bank:
    lda BANK_INFO,x
    beq @bank_pad
    jsr lcd_data
    inx
    cpx #20
    bne @bank
    jmp @machine
@bank_pad:
    lda #' '
    jsr lcd_data
    inx
    cpx #20
    bne @bank_pad
@machine:
    lda #$94
    jsr lcd_command
    ldx #0
@info:
    lda lcd_machine,x
    jsr lcd_data
    inx
    cpx #20
    bne @info
    lda #<lcd_ready
    ldy #>lcd_ready
    jmp lcd_status
lcd_title: .byte "AMC-6502 STATUS     "
lcd_machine: .byte "CPU 1MHz / RAM 32K   "
lcd_ready: .byte "READY",0

; Console output to shadow buffer, with normal top-to-bottom scrolling.
lcd_console:
    and #$7f
    cmp #13
    beq lcd_cr
    cmp #10
    beq lcd_lf
    cmp #12
    bne @not_clear
    jmp lcd_clear_internal
@not_clear:
    cmp #8
    beq lcd_backspace
    cmp #127
    beq lcd_backspace
    cmp #32
    bcc @done
    sta LCD_INDEX            ; temporarily preserve character
    lda #0
    sta LCD_CR
    lda LCD_COL
    cmp #20
    bcc @position
    jsr lcd_newline
@position:
    ldx LCD_ROW
    lda lcd_row_offsets,x
    clc
    adc LCD_COL
    ora #$80
    jsr lcd_command
    ldx LCD_ROW
    lda lcd_buffer_offsets,x
    clc
    adc LCD_COL
    tax
    lda LCD_INDEX
    sta LCD_BUFFER,x
    jsr lcd_data
    inc LCD_COL
@done:
    rts
lcd_cr:
    lda #0
    sta LCD_COL
    lda #1
    sta LCD_CR
    rts
lcd_lf:
    lda #0
    sta LCD_CR
    jmp lcd_newline
lcd_backspace:
    lda LCD_COL
    beq @done
    dec LCD_COL
@done:
    rts
lcd_newline:
    lda #0
    sta LCD_COL
    inc LCD_ROW
    lda LCD_ROW
    cmp #4
    bcc @done
    lda #3
    sta LCD_ROW
    ldx #0
@scroll:
    lda LCD_BUFFER+20,x
    sta LCD_BUFFER,x
    inx
    cpx #60
    bne @scroll
    lda #' '
@blank:
    sta LCD_BUFFER,x
    inx
    cpx #80
    bne @blank
    lda #0
    sta LCD_LINE_COUNT
@row:
    ldx LCD_LINE_COUNT
    lda lcd_row_offsets,x
    ora #$80
    jsr lcd_command
    ldx LCD_LINE_COUNT
    lda lcd_buffer_offsets,x
    sta LCD_NIBBLE_INDEX
    lda #20
    sta LCD_REDRAW_COUNT
@redraw:
    ldx LCD_NIBBLE_INDEX
    lda LCD_BUFFER,x
    jsr lcd_data
    inc LCD_NIBBLE_INDEX
    dec LCD_REDRAW_COUNT
    bne @redraw
    inc LCD_LINE_COUNT
    lda LCD_LINE_COUNT
    cmp #4
    bne @row
@done:
    rts
lcd_row_offsets: .byte $00,$40,$14,$54
lcd_buffer_offsets: .byte 0,20,40,60
LCD_NIBBLE_INDEX = $7fdd
LCD_REDRAW_COUNT = $7fde
