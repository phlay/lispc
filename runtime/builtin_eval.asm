%include "runtime.inc"
%include "panic.inc"


%ifdef DEBUG
extern __builtin_println
%endif

extern	__apply.continue


section .text

;
; builtin-wrapper for __eval below
;

		global	__builtin_eval
		global	__builtin_eval.continue

__builtin_eval:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rax
		jmp	__eval



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
%ifdef DEBUG
		push	rax
		push	rax	; dummy
		push	msg_eval
		push	rax
		mov	rcx, 2
		call	__builtin_println
		pop	rax
%endif

		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		test	rax, rbp		; leave type on for return value
		jz	.out
		cmp	dl, TYPE_CONS
		je	eval_cons
.out:		ret



eval_cons:	mov	rbx, rax
		and	rbx, rbp
		mov	rax, [rbx]

		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_QUOTE
		je	.handle_quote
		cmp	dl, TYPE_CONS
		je	.handle_cons
		cmp	dl, TYPE_LAMBDA
		je	.eval_params
		cmp	dl, TYPE_CLOSURE
		je	.eval_params
		jmp	__panic_type

.handle_quote:	mov	rax, [rbx + 8]		; just return first argument
		and	rax, rbp
		mov	rax, [rax]
		ret

.handle_cons:	push	rbx
		call	eval_cons
		pop	rbx

.eval_params:	mov	r8, rax			; this is hopefully a lambda
		xor	rcx, rcx		; count parameters in rcx

.push_params:	mov	rbx, [rbx + 8]		; load next entry in list
		mov	rdx, rbx		; dl <- type of parameter
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	rbx, rbp		; found end of parameter?
		jz	.apply
		cmp	dl, TYPE_CONS		; this must be a list!
		jne	__panic_type

		push	rbx
		push	rcx
		push	r8
		mov	rax, [rbx]		; eval [rbx] recursively
		call	__eval
		pop	r8
		pop	rcx
		pop	rbx
		push	rax			; push result on stack
		inc	rcx
		jmp	.push_params

.apply:		mov	rax, r8
		jmp	__apply.continue


section .data

%ifdef DEBUG
msg_eval		db "eval: ", 0
%endif
