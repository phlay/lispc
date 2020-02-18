%include "runtime.inc"
%include "syscall.inc"
%include "mem.inc"
%include "panic.inc"

extern	main
extern	__type_is_int

global	__start_stack

section .text

		global	_start

_start:		mov	rbp, MASK_ADDR

		mov	rsi, 64*1024*1024
		call	__mem_init

		mov	[__start_stack], rsp

		; we assume no parameter to main
		push	rax		; dummy
		call	main

		; if main returns an integer use it as return code
		xor	rdi, rdi
		call	__type_is_int
		jc	.exit
		mov	rdi, [rax]
.exit:		mov	rax, SYS_EXIT
		syscall




section .bss

__start_stack		resq	1
