%include "cell.inc"


section .text

;
; evaluates parameter
;
; input:
;	RAX	cell to evaluate
;
		global	__eval

__eval:
		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	rax, rbp
		jz	.out
		cmp	dl, TYPE_CONS
		je	eval_call
		cmp	dl, TYPE_INT
		je	.out
		cmp	dl, TYPE_REAL
		je	.out
		cmp	dl, TYPE_STR
		je	.out

		stc				; fail, if we do not know the type
		ret

.out:		clc
		ret


eval_call:	mov	rdi, rsp		; save stack pointer in case of error

		mov	rbx, [rax]		; fetch function
		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_LAMBDA
		jne	.errout
		and	rbx, rbp
		jz	.errout
		mov	r8, [rbx + 8]		; save expected number of parameter
		and	r8, rbp			; remove GC markings
		mov	rbx, [rbx]		; save function pointer
		xor	rcx, rcx

.push_params:	mov	rax, [rax + 8]		; load next
		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	rax, rbp		; check for NIL
		jz	.call
		cmp	dl, TYPE_CONS		; this must be a list!
		jne	.errout
		push	qword [rax]
		inc	rcx
		jmp	.push_params

.call:		cmp	r8, 65536
		jb	.check

		push	rcx			; push parameter count
.out:		push	rbx			; continue with our function
		ret

.check:		cmp	rcx, r8
		je	.out

.errout:	mov	rsp, rdi
		stc
		ret
