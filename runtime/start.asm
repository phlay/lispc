%include "syscall.inc"
%include "mem.inc"
%include "puts.inc"

extern	main

section .text


		global	_start
_start:
		mov	rsi, 16*1024*1024
		call	mem_init
		jc	.error_memory

		; we assume no parameter to main
		push	rax		; dummy
		call	main
		jc	.errexit

.exit:		mov	rax, SYS_EXIT
		xor	rdi, rdi
		syscall


.error_memory:	mov	rsi, msg_error_memory
		call	puts
.errexit:	mov	rax, SYS_EXIT
		xor	rdi, rdi
		inc	rdi
		syscall


section	.data

msg_error_memory	db "error: memory initialization failed", 0
