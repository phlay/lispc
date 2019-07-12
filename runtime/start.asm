%include "runtime.inc"
%include "syscall.inc"
%include "mem.inc"
%include "panic.inc"

extern	main

section .text


		global	_start

_start:		mov	rbp, MASK_ADDR

		mov	rsi, 64*1024*1024
		call	__mem_init
		jc	.panic_memory

		; we assume no parameter to main
		push	rax		; dummy
		call	main
		jc	.errexit

.exit:		mov	rax, SYS_EXIT
		xor	rdi, rdi
		syscall


.errexit:	mov	rax, SYS_EXIT
		xor	rdi, rdi
		inc	rdi
		syscall

.panic_memory:	lea	rsi, [msg_error_memory]
		call	__panic



section	.data

msg_error_memory	db "memory initialization failed", 0
