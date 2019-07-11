%include "cell.inc"

extern __builtin_println


section .text

;
; evaluates parameter
;
; input:
;	RAX	cell to evaluate
;
; output:
;	RAX	result of evaluation
;
		global	__eval

__eval:
		;;;;;;;;;;;;;;;;;;;;;;;;;;;;
		;push	rax
		;
		;push	rax	; dummy
		;push	msg_eval
		;push	rax	; parameter
		;push	qword 2
		;call	__builtin_println
		;
		;pop	rax
		;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		test	rax, rbp		; if NIL go out, leave type on
		jz	.out
		cmp	dl, TYPE_CONS
		je	eval_call

.out:		clc
		ret


eval_call:	mov	rdi, rsp		; save stack pointer in case of error
		and	rax, rbp

		mov	rbx, [rax]		; fetch lambda
		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_LAMBDA
		jne	.errout			; rbx must be a lambda
		and	rbx, rbp
		jz	.errout			; and not NIL
		mov	r8, [rbx + 8]		; r8 <- lambda argc
		and	r8, rbp
		mov	rbx, [rbx]		; rbx <- lambda code
		xor	rcx, rcx		; rcx is parameter counter

.push_params:	mov	rax, [rax + 8]		; load next
		mov	rdx, rax		; dl <- type of parameter
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	rax, rbp		; found end of parameter?
		jz	.call
		cmp	dl, TYPE_CONS		; this must be a list!
		jne	.errout

		;; now we evaluate [rax] recursively
		push	rax
		push	rbx
		push	rcx
		push	r8
		push	rdi

		mov	rax, [rax]
		call	__eval			; XXX carry

		pop	rdi
		pop	r8
		pop	rcx
		pop	rbx

		pop	rdx			; replace value on stack
		xchg	rax, rdx		; (old RAX) with current RAX
		push	rdx			; (= result of __eval)

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

section .data

msg_eval		db "eval: ", 0
