%include "runtime.inc"
%include "panic.inc"


%ifdef DEBUG
extern __builtin_println
%endif


section .text

;
; apply a lambda or closure to parameters given on stack
;
; input:
;	RAX	lambda or closure to call
;	RCX	number of parameter on stack
;
; output:
;	RAX	result of lambda
;

		global	__apply
		global	__apply.continue

__apply:	pop	rdx
		mov	[rsp + 8*rcx], rdx

.continue:

%ifdef DEBUG
		push	rax
		push	rcx

		push	rax	; dummy
		push	msg_apply
		push	rax
		mov	rcx, 2
		call	__builtin_println

		pop	rcx
		pop	rax
%endif

		mov	rdx, rax
		and	rax, rbp
		jz	__panic_nil
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_CLOSURE
		je	.closure
		jmp	.check_lambda

.closure:	mov	rbx, [rax + 8]
.push:		and	rbx, rbp
		jz	.closure_done
		push	qword [rbx]
		mov	rbx, [rbx + 8]
		jmp	.push

.closure_done:	mov	rax, [rax]		; load λ
		mov	rdx, rax
		and	rax, rbp
		jz	__panic_nil
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
.check_lambda:	cmp	dl, TYPE_LAMBDA
		jne	__panic_type
		mov	rdx, [rax + 8]		; get λ-argc
		and	rdx, rbp
		cmp	rdx, LAMBDA_VARIADIC
		je	.run
		cmp	rcx, rdx		; argc matches
		jne	__panic_argc
.run:		push	qword [rax]		; continue to λ
		ret

section .data

%ifdef DEBUG
msg_apply		db "apply: ", 0
%endif
