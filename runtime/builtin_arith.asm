%include "runtime.inc"
%include "mem.inc"

		global	__builtin_add
		global	__builtin_add.continue

__builtin_add:	pop	rax
		mov	[rsp + 8*2], rax

.continue:	call	pop_2_int
		jc	.out

		mov	rax, [rax]
		add	rax, [rbx]
		jc	.out
		jmp	__mem_int
.out:		ret


		global	__builtin_sub
		global	__builtin_sub.continue

__builtin_sub:	pop	rax
		mov	[rsp + 8*2], rax

.continue:	call	pop_2_int
		jc	.out

		mov	rax, [rax]
		sub	rax, [rbx]
		jc	.out
		jmp	__mem_int
.out:		ret



		global	__builtin_mul
		global	__builtin_mul.continue

__builtin_mul:	pop	rax
		mov	[rsp + 8*2], rax

.continue:	call	pop_2_int
		jc	.out

		mov	rax, [rax]
		mul	qword [rbx]
		test	rdx, rdx	; overflow check
		jnz	.errout
		jmp	__mem_int

.errout:	stc
.out:		ret


		global	__builtin_div
		global	__builtin_div.continue

__builtin_div:	pop	rax
		mov	[rsp + 8*2], rax

.continue:	call	pop_2_int
		jc	.out

		xor	rdx, rdx
		mov	rax, [rax]
		div	qword [rbx]
		jmp	__mem_int
.out:		ret



		global	__builtin_mod
		global	__builtin_mod.continue

__builtin_mod:	pop	rax
		mov	[rsp + 8*2], rax

.continue:	call	pop_2_int
		jc	.out

		xor	rdx, rdx
		mov	rax, [rax]
		div	qword [rbx]
		mov	rax, rdx
		jmp	__mem_int
.out:		ret



		global	__builtin_eq
		global	__builtin_eq.continue

__builtin_eq:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	call	pop_2_int
		jc	return_false
		mov	rax, [rax]
		cmp	rax, [rbx]
		je	return_true

return_false:	xor	rax, rax
		ret

return_true:	mov	al, TYPE_TRUE
		shl	rax, SHIFT_TYPE
		ret




		global	__builtin_gt
		global	__builtin_gt.continue

__builtin_gt:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	call	pop_2_int
		jc	return_false
		mov	rax, [rax]
		cmp	rax, [rbx]
		jg	return_true
		jmp	return_false



		global	__builtin_ge
		global	__builtin_ge.continue

__builtin_ge:	pop	rax
		mov	[rsp + 2*8], rax
.continue:	call	pop_2_int
		jc	return_false
		mov	rax, [rax]
		cmp	rax, [rbx]
		jge	return_true
		jmp	return_false



		global	__builtin_lt
		global	__builtin_lt.continue

__builtin_lt:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	call	pop_2_int
		jc	return_false
		mov	rax, [rax]
		cmp	rax, [rbx]
		jl	return_true
		jmp	return_false


		global	__builtin_le
		global	__builtin_le.continue

__builtin_le:	pop	rax
		mov	[rsp + 2*8], rax
.continue:	call	pop_2_int
		jc	return_false
		mov	rax, [rax]
		cmp	rax, [rbx]
		jle	return_true
		jmp	return_false



is_int:		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_INT
		jne	.errout
		and	rax, rbp
		jz	.errout
		clc
		ret
.errout:	stc
		ret


pop_2_int:	pop	rcx
		pop	rax
		pop	rbx
		push	rcx
		call	is_int
		jc	.out
		xchg	rax, rbx
		call	is_int
		jc	.out
.out:		ret
