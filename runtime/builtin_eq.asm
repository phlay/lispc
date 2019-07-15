%include "runtime.inc"
%include "panic.inc"

section .text

		global	__builtin_eq
		global	__builtin_eq.continue

__builtin_eq:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	pop	rsi
		pop	rdi

eq:		mov	rdx, rsi
		shr	rdx, 8
		or	rdx, rdi
		shr	rdx, SHIFT_TYPE - 8
		and	dx, 0x0f0f
		cmp	dh, dl
		jne	return_false

		and	rsi, rbp
		jz	.is_rdi_nil
		and	rdi, rbp
		jz	return_false

		test	dl, dl
		jz	cmp_ptr
		cmp	dl, TYPE_CONS
		je	cmp_cons
		cmp	dl, TYPE_INT
		je	cmp_int
		cmp	dl, TYPE_REAL
		je	cmp_real
		cmp	dl, TYPE_STR
		je	cmp_str
		cmp	dl, TYPE_LAMBDA
		je	cmp_ptr
		cmp	dl, TYPE_TRUE
		je	return_true
		cmp	dl, TYPE_QUOTE
		je	return_true

		jmp	__panic_type


.is_rdi_nil:	test	rdi, rbp
		jnz	return_false
return_true:	mov	al, TYPE_TRUE
		shl	rax, SHIFT_TYPE
		ret
return_false:	xor	rax, rax
		ret

cmp_ptr:	cmp	rsi, rdi
		je	return_true
		jmp	return_false

cmp_cons:	push	rsi
		push	rdi
		mov	rsi, [rsi]		; compare heads
		mov	rdi, [rdi]
		call	eq
		pop	rdi
		pop	rsi

		test	rax, rax		; false?
		jz	.out

		mov	rsi, [rsi + 8]
		mov	rdi, [rdi + 8]
		and	rsi, rbp
		jz	.found_rsi_end
		and	rdi, rbp
		jz	return_false
		jmp	cmp_cons

.found_rsi_end:	test	rdi, rbp
		jnz	return_false
		; rax is still true from last eq
.out:		ret



cmp_int:	mov	rax, [rsi]
		cmp	rax, [rdi]
		je	return_true
		jmp	return_false

cmp_real:	jmp	__panic_notyet

cmp_str:	mov	al, [rsi]
		inc	rsi
		mov	ah, [rdi]
		inc	rdi

		cmp	al, ah
		jne	return_false
		test	al, al
		jz	return_true

.reload_rsi:	test	sil, 0x07
		jnz	.reload_rdi
		mov	rsi, [rsi]
		and	rsi, rbp

.reload_rdi:	test	dil, 0x07
		jnz	cmp_str
		mov	rdi, [rdi]
		and	rdi, rbp
		jmp	cmp_str

