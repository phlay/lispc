%include "cell.inc"

		global	builtin_head
		global	builtin_head.continue

builtin_head:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rbx
		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_CONS
		jne	.errout

		and	rbx, rbp	; extract address
		jz	.errout		; got NIL

		mov	rax, [rbx]	; rax <- head
		clc
		ret

.errout:	stc
		ret
