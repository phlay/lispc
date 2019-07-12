		global	__builtin_quote
		global	__builtin_quote.continue

__builtin_quote:
		pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rax
		clc
		ret
