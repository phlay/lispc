%include "runtime.inc"
%include "syscall.inc"
%include "panic.inc"
%include "start.inc"


section .text
;
; initialize memory pool
;
; RSI	number cells to allocate in pool
;
;
		global	__mem_init
__mem_init:
		; use mmap to allocate memory
		mov	rax, SYS_MMAP
		xor	rdi, rdi				; addr
		shl	rsi, 4					; length
		mov	rdx, PROT_READ | PROT_WRITE		; prot
		mov	r10, MAP_PRIVATE | MAP_ANONYMOUS	; flags
		xor	r8, r8					; fd
		dec	r8
		xor	r9, r9					; offset
		syscall
		mov	rbx, rax	; check for MAP_FAILED = -1
		inc	rbx
		jz	__panic_memory

		mov	[pool], rax
		mov	[next_free], rax
		add	rax, rsi
		mov	[pool_end], rax

		ret


;
; allocates a new cell from pool
;
; output:
;	RDI	address of new cell without any type information
;
; changes: rdx, rdi, r8, r9, r10b
;
		global	__mem_alloc

__mem_alloc:	xor	r10b, r10b
		mov	rdi, [next_free]
.search:	cmp	rdi, [pool_end]
		jae	.need_gc

.check_free:	mov	rdx, [rdi + 8]
		rcl	rdx, 1
		jnc	.return

		mov	rdx, [rdi + 8]		; mark as free and continue
		shl	rdx, 1
		shr	rdx, 1
		mov	[rdi + 8], rdx
		add	rdi, 16
		jmp	.search


.need_gc:	test	r10b, r10b		; did we already collect?
		jnz	__panic_oom

		lea	r8, [rsp + 8]
.mark_stack:	cmp	r8, [__start_stack]
		jae	.done_marking
		mov	r9, [r8]
		call	mark
		add	r8, 8
		jmp	.mark_stack

.done_marking:	mov	rdi, [pool]		; restart at beginning
		inc	r10b
		jmp	.check_free

.return:	mov	r8, rdi
		add	r8, 16
		mov	[next_free], r8
		ret


;
; mark memory as beeing in use
;
; input:
;	R9	cell to mark
;
; changes: rdx, rdi, r9
;
mark:		mov	rdx, r9
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	r9, rbp
		jz	.out
		test	dl, dl
		jz	.out

		mov	rdi, [r9 + 8]		; mark this cell
		shl	rdi, 1
		stc
		rcr	rdi, 1
		mov	[r9 + 8], rdi

		cmp	dl, TYPE_CONS
		je	.mark_cons
		cmp	dl, TYPE_STR
		je	.mark_str
.out:		ret

.mark_cons:	push	r9
		mov	r9, [r9]
		call	mark
		pop	r9
.mark_str:	mov	r9, [r9 + 8]
		jmp	mark




;
; allocate integer cell
;
; input:
;	RAX	integer to put into cell
;
; returns:
;	RAX	cell holding integer
;
		global	__mem_int

__mem_int:	call	__mem_alloc

		mov	[rdi], rax		; left  <- integer
		xor	rax, rax		; right <- null
		mov	[rdi + 8], rax

		mov	al, TYPE_INT
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		ret



; alloctes a lisp string from a buffer
;
; input:
;	RSI	string pointer
;	RBX	string length
;
; output:
;	RAX	cell with string
;
		global	__mem_string

__mem_string:	xor	rdi, rdi
		test	rbx, rbx		; use shortcut if empty
		jz	.loop

		lea	rsi, [rsi + rbx - 1]	; go to end of string
		std

		call	__mem_alloc		; allocate last string block
		xor	rdx, rdx
		mov	[rdi], rdx		; zero fill
		mov	[rdi + 8], rdx		; and NIL termination

		xor	rcx, rcx		; rcx <- rbx mod 8
		mov	cl, bl
		and	cl, 0x07
		jz	.full_block		; do we need a partial block?

		sub	rbx, rcx		; copy last bytes of str
		lea	rdi, [rdi + rcx - 1]
		rep	movsb
		inc	rdi

.loop:		mov	al, TYPE_STR		; rax <- type marked rdi
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		test	rbx, rbx		; done yet?
		jz	.out

		push	rax			; save current result on stack
		call	__mem_alloc
		pop	qword [rdi + 8]		; link old string in

.full_block:	mov	rcx, 8			; fill full 8 byte block
		sub	rbx, rcx
		lea	rdi, [rdi + rcx - 1]
		rep	movsb
		inc	rdi
		jmp	.loop

.out:		ret


;
; allocate a cell holding a lambda
;
; input:
;	RSI	pointer to lambda code
;	RBX	number of parameters, < LAMBDA_VARIADIC
;		(or equal to LAMBDA_VARIADIC for variadic function)
;
; output:
;	RAX	cell holding the lambda
;

		global	__mem_lambda

__mem_lambda:	call	__mem_alloc

		mov	[rdi], rsi
		mov	[rdi + 8], rbx

		mov	al, TYPE_LAMBDA
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		ret



section .bss

pool		resq	1
pool_end	resq	1
next_free	resq	1
