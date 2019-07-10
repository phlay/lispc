%include "cell.inc"

		global	builtin_tail
		global	builtin_tail.continue

builtin_tail:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rbx
		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_CONS
		jne	.errout

		and	rbx, rbp		; is it NIL?
		jz	.errout

		mov	rax, [rbx + 8]
		clc
		ret

.errout:	stc
		ret
