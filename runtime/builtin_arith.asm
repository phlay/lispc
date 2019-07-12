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
		mov	rbx, [rbx]
		div	rbx
		jmp	__mem_int
.out:		ret




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
