.setcpu "6502"
.include "fw.inc"
COUT = FW_COUT
CIN = FW_CIN
IRQ_VECTOR = FW_IRQ_VECTOR
SAVED = $02f4
IRQ_COUNT = $02f5
FAILURES = $02f6
TIMER_FLAG = $02f7
TIMER_LOW = $02f8
PTR = $00
VIA = $02
.segment "CODE"
entry:
    sei
    lda #<irq_handler
    sta IRQ_VECTOR
    lda #>irq_handler
    sta IRQ_VECTOR+1
rerun:
    sei
    lda #<lcd_testing
    ldy #>lcd_testing
    jsr FW_LCD_STATUS
    lda #0
    sta FAILURES
    lda #<banner
    ldy #>banner
    jsr puts
    jsr ram_test
    bcc @ram_ok
    inc FAILURES
    lda #<ram_fail
    ldy #>ram_fail
    jmp @ram_report
@ram_ok:
    lda #<ram_pass
    ldy #>ram_pass
@ram_report:
    jsr puts
    lda #>VIA1_BASE
    sta VIA+1
    lda #0
    sta VIA
    lda #<via1
    ldy #>via1
    jsr puts
    jsr via_tests
    lda #>VIA2_BASE
    sta VIA+1
    lda #<VIA2_BASE
    sta VIA
    lda #<via2
    ldy #>via2
    jsr puts
    jsr via_tests
    lda FAILURES
    bne @failed
    lda #<all_pass
    ldy #>all_pass
    jmp @summary
@failed:
    lda #<some_failed
    ldy #>some_failed
@summary:
    jsr FW_LCD_STATUS
    jsr puts
menu:
    lda #<prompt
    ldy #>prompt
    jsr puts
@key:
    jsr CIN
    cmp #'L'
    beq @load
    cmp #'l'
    beq @load
    cmp #'R'
    beq rerun
    cmp #'r'
    beq rerun
    jmp @key

@load:
    jsr FW_LOAD
    jmp menu

; Restore each byte immediately. Workspace ZP $00-$05 / $02F0-$02F8 is excluded.
ram_test:
    lda #0
    sta PTR
    lda #3
    sta PTR+1
    ldy #0
@byte:
    lda (PTR),y
    sta SAVED
    ldx #1
@pattern:
    lda patterns,x
    sta (PTR),y
    cmp (PTR),y
    bne @fail
    dex
    bpl @pattern
    lda SAVED
    sta (PTR),y
    iny
    beq @page
    lda PTR+1
    cmp #$7f
    bne @byte
    cpy #$80
    bne @byte
    clc
    rts
@page:
    inc PTR+1
    lda PTR+1
    cmp #$80
    bne @byte
    clc
    rts
@fail:
    lda SAVED
    sta (PTR),y
    sec
    rts

via_tests:
    lda #$40
    sta TIMER_FLAG
    lda #4
    sta TIMER_LOW
    jsr timer_test
    jsr result
    lda #<t1
    ldy #>t1
    jsr puts
    lda #$20
    sta TIMER_FLAG
    lda #8
    sta TIMER_LOW
    jsr timer_test
    jsr result
    lda #<t2
    ldy #>t2
    jmp puts
result:
    bcs @fail
    lda #<pass
    ldy #>pass
    jmp puts
@fail:
    inc FAILURES
    lda #<fail
    ldy #>fail
    jmp puts

; Bounded polling: flag must set while masked, then enabled IRQ must reach handler.
; No peripheral port output reconfiguration: serial and attached expansion stay intact.
timer_test:
    sei
    ldy #14
    lda #$7f
    sta (VIA),y
    ldy #11
    lda #0
    sta (VIA),y
    ldy #13
    lda #$7f
    sta (VIA),y
    lda #0
    sta IRQ_COUNT
    ldy TIMER_LOW
    lda #64
    sta (VIA),y
    iny
    lda #0
    sta (VIA),y
    ldx #$ff
    ldy #13
@flag:
    lda (VIA),y
    and TIMER_FLAG
    bne @pending
    dex
    bne @flag
    jmp @fail
@pending:
    lda (VIA),y
    bmi @fail                 ; disabled sources must not assert summary IRQ
    ldy #14
    lda TIMER_FLAG
    ora #$80
    sta (VIA),y
    cli
    ldx #$ff
@irq:
    lda IRQ_COUNT
    bne @received
    dex
    bne @irq
    jmp @fail
@received:
    sei
    jsr cleanup
    clc
    rts
@fail:
    sei
    jsr cleanup
    sec
    rts
cleanup:
    ldy #14
    lda #$7f
    sta (VIA),y
    ldy #13
    sta (VIA),y
    rts

irq_handler:
    pha
    lda VIA1_BASE+$d
    and #$60
    bne @ack
    lda VIA2_BASE+$d
    and #$60
    beq @return
@ack:
    lda VIA1_BASE+$4
    lda VIA1_BASE+$8
    lda VIA2_BASE+$4
    lda VIA2_BASE+$8
    inc IRQ_COUNT
@return:
    pla
    rti

puts:
    jmp FW_PUTS
patterns: .byte $55,$aa
banner: .byte 13,10,"AMC-6502 DIAGNOSTICS - BANK 3",13,10,0
ram_pass: .byte "PASS RAM $0300-$7F7F (restored)",13,10,0
ram_fail: .byte "FAIL RAM $0300-$7F7F",13,10,0
via1: .byte "VIA 1",13,10,0
via2: .byte "VIA 2",13,10,0
pass: .byte "PASS ",0
fail: .byte "FAIL ",0
t1: .byte "T1 + IRQ",13,10,0
t2: .byte "T2 + IRQ",13,10,0
all_pass: .byte "ALL CHECKS PASS",13,10,0
some_failed: .byte "DIAGNOSTIC FAILURE",13,10,0
prompt: .byte "R to rerun / L load HEX",13,10
    .byte "Hold RESET, set bank toggles, release RESET to change ROM.",13,10,0

lcd_testing: .byte "TESTING RAM / VIAs",0
