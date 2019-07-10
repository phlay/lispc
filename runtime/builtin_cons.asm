%include "cell.inc"
%include "mem.inc"

		global	__builtin_cons
		global	__builtin_cons.continue

__builtin_cons:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	pop	rbx
		pop	rax
		jmp	__mem_cons
