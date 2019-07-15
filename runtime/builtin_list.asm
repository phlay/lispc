extern	__cons

		global	__builtin_list
		global	__builtin_list.continue

__builtin_list:
		pop	rax
		mov	[rsp + 8*rcx], rax

.continue:	xor	rax, rax

.cons:		mov	rbx, rax
		pop	rax
		call	__cons
		loop	.cons
		ret
