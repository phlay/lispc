%include "syscall.inc"
%include "puts.inc"
%include "putc.inc"

section	.text

;
; panic - display message and exit with error level 1
;
;	rsi	error message to display
;
		global	__panic

__panic:	push	rsi
		mov	rsi, panic_msg
		call	__puts
		pop	rsi
		call	__puts
		call	__putnl

		mov	rax, SYS_EXIT
		xor	rdi, rdi
		inc	rdi
		syscall


section .data

panic_msg	db "Error: ", 0
