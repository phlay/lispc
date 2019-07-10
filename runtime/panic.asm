%include "syscall.inc"
%include "puts.inc"
%include "putc.inc"

section	.text

;
; panic - display message and exit with error level 1
;
;	rsi	error message to display
;
		global	panic

panic:		push	rsi
		mov	rsi, panic_msg
		call	puts
		pop	rsi
		call	puts
		call	putnl

		mov	rax, SYS_EXIT
		xor	rdi, rdi
		inc	rdi
		syscall


section .data

panic_msg:	db "Error: ", 0
