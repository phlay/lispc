%include "runtime.inc"
%include "panic.inc"

section .text

;
; apply a lambda to parameter given to this function
;
; input:
;	RAX	lambda to call
;	RCX	number of parameter on stack
;
; output:
;	RAX	result of lambda
;

		global	__apply
		global	__apply.continue

__apply:	pop	rbx
		mov	[rsp + 8*rcx], rbx

.continue:	mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_LAMBDA
		jne	__panic_type
		and	rax, rbp
		jz	__panic_nil
		mov	rdx, [rax + 8]		; get λ-argc
		and	rdx, rbp
		cmp	rdx, LAMBDA_VARIADIC
		je	.out
		cmp	rcx, rdx		; argc matches
		jne	__panic_argc

.out:		push	qword [rax]		; continue to λ
		ret
