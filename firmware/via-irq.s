.setcpu "6502"
.include "hardware.inc"
.segment "CODE"
reset:
    sei
    cld
    ldx #$ff
    txs
    lda #0
    sta $0200
    sta $0201
    sta $0202
    sta $0203
    lda #$c0
    sta VIA1_BASE+$e             ; VIA1 enable T1
    lda #30
    sta VIA1_BASE+$4
    lda #0
    sta VIA1_BASE+$5
    ldx #30               ; let T1 expire while CPU I flag masks IRQ
@masked:
    dex
    bne @masked
    lda VIA1_BASE+$d
    sta $0202             ; must capture pending, enabled T1: $C0
    cli
@t1:
    lda $0200
    beq @t1
    lda #$a0
    sta VIA2_BASE+$e             ; VIA2 enable T2
    lda #30
    sta VIA2_BASE+$8
    lda #0
    sta VIA2_BASE+$9
@t2:
    lda $0201
    beq @t2
    sei
    lda #$42
    sta $0203
@done:
    jmp @done
.segment "HANDLER"
irq:
    pha
    lda VIA1_BASE+$d
    and #$40
    beq @check2
    lda VIA1_BASE+$4             ; acknowledge T1
    inc $0200
@check2:
    lda VIA2_BASE+$d
    and #$20
    beq @return
    lda VIA2_BASE+$8             ; acknowledge T2
    inc $0201
@return:
    pla
    rti
.segment "VECTORS"
    .word irq, reset, irq
