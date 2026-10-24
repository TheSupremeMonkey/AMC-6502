.setcpu "6502"
.segment "CODE"
reset:
    sei
    cld
    ldx #$ff
    txs
    lda #$00
    sta $0200             ; clear completion marker on every reset
    lda #$55
    sta $0000
    sta $7fff
    lda #$aa
    sta $0100
    lda $0000
    cmp #$55
    bne failed
    lda $7fff
    cmp #$55
    bne failed
    lda $0100
    cmp #$aa
    bne failed
    lda #$00
    sta reset             ; attempted ROM write must have no effect
    lda reset
    cmp #$78              ; SEI opcode
    bne failed
    lda #$42
    sta $0200
done:
    jmp done
failed:
    lda #$ff
    sta $0200
    jmp failed
interrupt:
    rti
.segment "VECTORS"
    .word interrupt, reset, interrupt
