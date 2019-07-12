%include "runtime.inc"

extern __true

section .text

		global	__builtin_not
		global	__builtin_not.continue

__builtin_not:	pop	rax
		mov	[rsp + 8], rax

.continue:	pop	rax
		call	__true
		jc	return_true

return_false:	xor	rax, rax
		ret



		global	__builtin_and
		global	__builtin_and.continue

__builtin_and:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	pop	rax
		pop	rbx

		call	__true
		jc	return_false

		mov	rax, rbx
		call	__true
		jc	return_false

return_true:	mov	al, TYPE_TRUE
		shl	rax, SHIFT_TYPE
		ret


		
		global	__builtin_or
		global	__builtin_or.continue

__builtin_or:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	pop	rax
		pop	rbx

		call	__true
		jnc	return_true
		mov	rax, rbx
		call	__true
		jnc	return_true
		jmp	return_false
