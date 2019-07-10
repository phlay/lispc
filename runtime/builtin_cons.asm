%include "cell.inc"
%include "mem.inc"

		global	builtin_cons
		global	builtin_cons.continue

builtin_cons:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	pop	rbx
		pop	rax
		jmp	mem_cons
