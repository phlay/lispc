%include "putc.inc"

section .text

; puts - print zero terminated sting to stdout using putc
;
; rsi	string to print
;
; changes: rax, rdi, rdx
;
		global	puts

puts_loop:	call	putc
		inc	rsi
puts:		cmp	byte [rsi], 0
		jne	puts_loop
		ret
