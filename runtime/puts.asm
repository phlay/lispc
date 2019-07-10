%include "putc.inc"

section .text

; print zero terminated sting to stdout using putc
;
; rsi	string to print
;
		global	__puts

puts_loop:	call	__putc
		inc	rsi
__puts:		cmp	byte [rsi], 0
		jne	puts_loop
		ret
