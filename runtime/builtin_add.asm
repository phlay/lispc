%include "runtime.inc"
%include "mem.inc"

		global	__builtin_add
		global	__builtin_add.continue

__builtin_add:	pop	rax
		mov	[rsp + 8*2], rax

.continue:	pop	rbx		; parameter 2
		pop	rax		; parameter 1

		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_INT
		jne	.errout
		and	rax, rbp
		jz	.errout

		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_INT
		jne	.errout
		and	rbx, rbp
		jz	.errout

		mov	rax, [rax]
		add	rax, [rbx]
		jc	.errout
		jmp	__mem_int


.errout:	stc
		ret
