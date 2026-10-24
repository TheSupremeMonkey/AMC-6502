; Intel HEX loader. All scratch fits inside the existing shared line buffer.
LENGTH = FW_LINEBUF+100
BAD = FW_LINEBUF+101
COUNT = FW_LINEBUF+102
KIND = FW_LINEBUF+103
SUM = FW_LINEBUF+104
TEMP = FW_LINEBUF+105
DATA = FW_LINEBUF+64
loader:
    php
    sei
    cld
    lda #<load_ready
    ldy #>load_ready
    jsr puts
load_next:
    lda #0
    sta LENGTH
    sta BAD
@char:
    jsr cin
    cmp #27
    beq load_abort
    cmp #13
    beq load_parse
    jsr cout                  ; echo is the per-character flow-control acknowledgement
    ldx LENGTH
    cpx #43                   ; : + 5 header/checksum bytes + 16 data bytes
    bcs @overflow
    sta FW_LINEBUF,x
    inc LENGTH
    jmp @char
@overflow:
    lda #1
    sta BAD
    jmp @char
load_abort:
    lda #<load_aborted
    ldy #>load_aborted
    jsr puts
    plp
    lda #1
    sec
    rts
load_parse:
    jsr crlf
    lda BAD
    bne load_error
    lda FW_LINEBUF
    cmp #':'
    bne load_error
    ldx #1
    lda #0
    sta SUM
    jsr load_byte
    bcs load_error
    cmp #17
    bcs load_error
    sta COUNT
    asl a
    clc
    adc #11
    cmp LENGTH
    bne load_error
    jsr load_byte
    bcs load_error
    sta FW_STRPTR+1
    jsr load_byte
    bcs load_error
    sta FW_STRPTR
    jsr load_byte
    bcs load_error
    sta KIND
    ldy #0
@data:
    cpy COUNT
    beq @checksum
    jsr load_byte
    bcs load_error
    sta DATA,y
    iny
    bne @data
@checksum:
    jsr load_byte
    bcs load_error
    lda SUM
    bne load_error
    lda KIND
    beq load_write
    cmp #1
    bne load_error
    lda COUNT
    ora FW_STRPTR
    ora FW_STRPTR+1
    bne load_error
    lda #<load_done
    ldy #>load_done
    jsr puts
    plp
    lda #0
    clc
    rts
load_error:
    lda #<load_err
    ldy #>load_err
    jsr puts
    jmp load_next
load_write:
    lda FW_STRPTR+1
    cmp #3
    bcc load_error
    cmp #$80
    bcs load_error
    ; Validate exclusive end, including carry and crossing FW_USER_END, before any store.
    clc
    lda FW_STRPTR
    adc COUNT
    tay
    lda FW_STRPTR+1
    adc #0
    cmp #>FW_USER_END
    bcc @valid
    bne load_error
    cpy #<FW_USER_END
    bcc @valid
    bne load_error
@valid:
    ldy #0
@copy:
    cpy COUNT
    beq @ok
    lda DATA,y
    sta (FW_STRPTR),y
    iny
    bne @copy
@ok:
    lda #<load_ok
    ldy #>load_ok
    jsr puts
    jmp load_next
; X is ASCII offset; Y preserved. C=1 invalid hex, else A decoded byte.
load_byte:
    jsr load_nibble
    bcs @return
    asl a
    asl a
    asl a
    asl a
    sta TEMP
    jsr load_nibble
    bcs @return
    ora TEMP
    pha
    clc
    adc SUM
    sta SUM
    pla
    clc
@return:
    rts
load_nibble:
    lda FW_LINEBUF,x
    inx
    cmp #'0'
    bcc @bad
    cmp #'9'+1
    bcc @decimal
    and #$df
    cmp #'A'
    bcc @bad
    cmp #'F'+1
    bcs @bad
    sec
    sbc #'A'-10
    clc
    rts
@decimal:
    sec
    sbc #'0'
    clc
    rts
@bad:
    sec
    rts
load_ready: .byte "HEX READY",13,10,0
load_ok: .byte "OK",13,10,0
load_err: .byte "ERR",13,10,0
load_done: .byte "DONE",13,10,0
load_aborted: .byte "ABORT",13,10,0
