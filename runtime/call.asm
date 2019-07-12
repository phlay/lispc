%include "runtime.inc"

section .text

;
; call a lambda
;
; input:
;	RAX	lambda to call
;	RCX	number of parameter on stack
;
; output:
;	RAX	result of lambda
;

		global	__call
		global	__call.continue

__call:		pop	rbx
		mov	[rsp + 8*rcx], rbx

.continue:	mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_LAMBDA
		jne	.errout
		and	rax, rbp
		jz	.errout
		mov	rdx, [rax + 8]		; get λ-argc
		and	rdx, rbp
		cmp	rdx, LAMBDA_VARIADIC
		je	.out
		cmp	rcx, rdx		; argc matches
		jne	.errout

.out:		push	qword [rax]		; continue to λ
		ret

.errout:	lea	rsp, [rsp + 8*rcx]	; clear stack
		stc
		ret

