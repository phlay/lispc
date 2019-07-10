%include "syscall.inc"


section .text

; print character on stdout
;
; rsi	pointer to character to print
;
		global	__putc

__putc:		mov	rax, SYS_WRITE
		mov	rdi, FD_STDOUT
		mov	rdx, 1
		syscall
		ret


		global	__putnl

__putnl:	lea	rsi, [char_nl]
		call	__putc
		ret


		global	__putsp

__putsp:	lea	rsi, [char_space]
		call	__putc
		ret


section .data

char_nl		db `\n`
char_space	db ` `
