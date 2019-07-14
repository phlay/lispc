%include "runtime.inc"
%include "panic.inc"

		global	__builtin_tail
		global	__builtin_tail.continue

__builtin_tail:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rbx
		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_CONS
		jne	__panic_type
		and	rbx, rbp
		jz	__panic_nil

		mov	rax, [rbx + 8]
		ret
