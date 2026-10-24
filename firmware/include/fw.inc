; AMC shared firmware ABI 0.4.0. Existing vectors are append-only.
.ifndef AMC_FW_INCLUDED
AMC_FW_INCLUDED = 1
.include "hardware.inc"
FW_COUT         = $e100
FW_CIN          = $e103
FW_BANK_SELECT  = $e106
FW_PUTS         = $e109
FW_HEX8         = $e10c
FW_HEX16        = $e10f
FW_READLINE     = $e112
FW_CIN_POLL     = $e115
FW_VERSION      = $e118
FW_BANK_GET     = $e11b
FW_CRLF         = $e11e
FW_LOAD         = $e121
FW_LCD_MODE      = $e124
FW_LCD_CLEAR     = $e127
FW_LCD_STATUS    = $e12a
FW_VERSION_MAJOR = 0
FW_VERSION_MINOR = 4
FW_VERSION_PATCH = 0
; Kernel-owned RAM; personalities must not allocate these bytes.
FW_STRPTR       = $f0           ; $F0-$F1, transient PUTS pointer
FW_LINEBUF      = $0280         ; $0280-$02EF, 111 characters + NUL
FW_LINE_MAX     = 111
FW_TX_SCRATCH   = $02f0
FW_RX_SCRATCH   = $02f1
FW_IRQ_VECTOR   = $02f2         ; two bytes, writable IRQ hook
; $02F4-$02F8 belong to bank 3 diagnostics, not the kernel.
FW_LINE_LIMIT   = $02f9
FW_LINE_LENGTH  = $02fa
FW_SKIP_LF      = $02fb
FW_PORTA_SHADOW = $02fc        ; all Port A output writers must maintain this latch shadow
FW_LCD_REQUEST  = $02fd        ; firmware-serviced mode request: 0 off,1 mirror,2 dashboard
FW_USER_END     = $7f80        ; exclusive: upper 128 bytes reserved for LCD
FW_BANK_INFO    = $ffc0
FW_BANK_INFO_SIZE = 32
.endif
