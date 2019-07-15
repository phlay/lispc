%include "runtime.inc"
%include "syscall.inc"
%include "mem.inc"
%include "panic.inc"

extern	main

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

		; XXX ignore return value for now
		xor	rdi, rdi
		mov	rax, SYS_EXIT
		syscall


section .bss

__start_stack		resq	1
