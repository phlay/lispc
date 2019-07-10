%include "syscall.inc"


section .text

; putc - print character on stdout
;
; rsi	pointer to character to print
;
		global putc

putc:		mov	rax, SYS_WRITE
		mov	rdi, FD_STDOUT
		mov	rdx, 1
		syscall
		ret


		global putnl
putnl:		mov	rsi, char_nl
		call	putc
		ret

		global	putsp
putsp:		mov	rsi, char_space
		call	putc
		ret


section .data

char_nl		db `\n`
char_space	db ` `
