%include "syscall.inc"

%include "panic.inc"
%include "cell.inc"

section .text
;
; initialize memory pool
;
; RSI	number cells to allocate in pool
;
;
		global	mem_init
mem_init:
		; use mmap to allocate memory
		mov	rax, SYS_MMAP
		xor	rdi, rdi				; addr
		shl	rsi, 4					; length
		mov	rdx, PROT_READ | PROT_WRITE		; prot
		mov	r10, MAP_PRIVATE | MAP_ANONYMOUS	; flags
		mov	r8, -1					; fd
		mov	r9, 0					; offset
		syscall
		cmp	eax, MAP_FAILED
		je	.errout
		test	rax, rax
		je	.errout

		mov	[_pool], rax
		mov	[_next_free], rax
		add	rax, rsi
		mov	[_pool_end], rax

		mov	rbp, MASK_ADDR

		clc
		ret
.errout:	stc
		ret


;
; mem_alloc - allocates a new cell from pool
;
; output:
;	rdi	address of new cell without any type information
;

		global	mem_alloc
mem_alloc:
		mov	rdi, [_next_free]

		;
		; XXX check used
		;

		jmp	.out


		;
		; XXX garbage collect
		;
		;; start searching from beginning again
		; mov	rax, [_pool]
		;
		;; search stack for values to mark
		;

		; collecting garbage did not help => die
		mov	rdi, mem_oom_msg
		call	panic
		; not reached


.out:		mov	r8, rdi
		add	r8, 16
		mov	[_next_free], r8
		ret




;
; mem_cons
;
; input:
;	RAX	cell x
;	RBX	cell y
;
; output:
;	RAX	( cons x y )
;
		global	mem_cons

mem_cons:	call	mem_alloc		; allocate cell

		mov	[rdi], rax		; left
		mov	[rdi + 8], rbx		; right

		mov	al, TYPE_CONS		; mark address with info
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		clc
		ret



;
; mem_int - allocate integer cell
;
; input:
;	RAX	integer to put into cell
;
; returns:
;	RAX	cell holding integer
;
		global	mem_int

mem_int:	call	mem_alloc

		mov	[rdi], rax		; left  <- integer
		xor	rax, rax		; right <- null
		mov	[rdi + 8], rax

		mov	al, TYPE_INT
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		clc
		ret




; mem_string - alloctes a lisp string
;
; input:
;	RSI	string pointer
;	RBX	string length
;
; output:
;	RAX	cell with string
;

		global	mem_string

mem_string:	lea	rsi, [rsi + rbx - 1]	; go to end of string
		std

		call	mem_alloc		; allocate last string block
		xor	rdx, rdx
		mov	[rdi], rdx		; zero fill
		mov	[rdi + 8], rdx		; and NIL termination

		xor	rcx, rcx		; rcx <- rbx mod 8
		mov	cl, bl
		and	cl, 0x07

		test	cl, cl			; do we need this?
		jz	.full_block

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
		call	mem_alloc
		pop	qword [rdi + 8]		; link old string in

.full_block:	mov	rcx, 8			; fill full 8 byte block
		sub	rbx, rcx
		lea	rdi, [rdi + rcx - 1]
		rep	movsb
		inc	rdi
		jmp	.loop

.out:		clc
		ret




section .data

mem_oom_msg:	db "out of memory", 0



section .bss

_pool		resq	1
_pool_end	resq	1
_next_free	resq	1
