; Assembled API integration fixture. Host seeds mode/arguments before reset entry.
.setcpu "6502"
.include "fw.inc"
.segment "CODE"
    ldx $0200
    lda dispatch_lo,x
    sta $06
    lda dispatch_hi,x
    sta $07
    jmp ($0006)
dispatch_lo: .byte <output_test,<line_test,<poll_test,<string_test,<line_twice
dispatch_hi: .byte >output_test,>line_test,>poll_test,>string_test,>line_twice
output_test:
    lda #<message
    ldy #>message
    ldx #$5a
    sta $0300
    stx $0301
    sty $0302
    jsr FW_PUTS
    sta $0303
    stx $0304
    sty $0305
    php
    pla
    sta $0306
    lda #$ab
    ldx #$37
    ldy #$6b
    sed
    jsr FW_HEX8
    sta $0307
    php
    pla
    sta $0315
    stx $0308
    sty $0309
    lda #$34
    ldy #$12
    ldx #$9a
    jsr FW_HEX16
    sta $030a
    stx $030b
    sty $030c
    cld
    jsr FW_CRLF
    jsr FW_VERSION
    sta $030d
    stx $030e
    sty $030f
    jsr FW_BANK_GET
    sta $0310
    stx $0313
    sty $0314
    jmp complete
line_test:
    lda $0201
    ldy #$6b
    jsr FW_READLINE
    jmp result
line_twice:
    lda $0201
    ldy #$6b
    jsr FW_READLINE
    stx $0312
    ldx #0
@copy:
    lda FW_LINEBUF,x
    sta $0400,x
    inx
    cmp #0
    bne @copy
    lda $0201
    ldy #$6b
    jsr FW_READLINE
    jmp result
poll_test:
    ldx #$37
    ldy #$6b
    jsr FW_CIN_POLL
    bcs @received
    sta $0204
    stx $0205
    sty $0206
    php
    pla
    sta $0207
    lda #$11
    sta $020e
@poll:
    jsr FW_CIN_POLL
    bcc @poll
@received:
    jmp result
string_test:
    lda $0202
    ldy $0203
    ldx #$5a
    jsr FW_PUTS
result:
    sta $0204
    stx $0205
    sty $0206
    php
    pla
    sta $0207
complete:
    lda #$42
    sta $020f
@done:
    jmp @done
message: .byte "ABI READY: ",0
