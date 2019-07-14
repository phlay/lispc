%include "runtime.inc"
%include "panic.inc"

		global	__builtin_head
		global	__builtin_head.continue

__builtin_head:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rbx
		mov	rdx, rbx
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_CONS
		jne	__panic_type

		and	rbx, rbp	; extract address
		jz	__panic_nil	; got NIL

		mov	rax, [rbx]	; rax <- head
		ret
