%include "runtime.inc"
%include "mem.inc"

		global	__builtin_atom
		global	__builtin_atom.continue

__builtin_atom:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rax
		test	rax, rbp
		jz	.true
		shr	rax, SHIFT_TYPE
		and	al, BYTEMASK_TYPE
		cmp	al, TYPE_CONS
		je	.false

.true:		mov	al, TYPE_TRUE
		shl	rax, SHIFT_TYPE
		ret

.false:		xor	rax, rax
		ret





