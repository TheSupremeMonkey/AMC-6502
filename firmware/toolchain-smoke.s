; Toolchain probe, not yet a full AMC-6502 firmware diagnostic.
.setcpu "6502"
.segment "CODE"
reset:
    sei
    cld
    ldx #$ff
    txs
    lda #$40
    clc
    adc #$02
    sta $0200
done:
    jmp done
interrupt:
    rti
.segment "VECTORS"
    .word interrupt, reset, interrupt
