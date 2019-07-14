%include "puts.inc"

section .text


; print decimal number
;
; rax		number to print
;

		global __printnum10

__printnum10:	mov	rbx, 10


; print number using putc
;
; rax		number to print
; rbx		radix with 0 < rbx <= 10
;
; changes: rax (=0), rcx, rdx, rsi, rdi
;
		global	__printnum

__printnum:	lea	rsi, [buffer]

		; in case of non-negative number go right into recursion
		; but skip the intro check (so zero gets printed).
		test	rax, rax
		jge	.skipcheck

		neg	rax			; make rax positive
		push	rax			; and print minus
		mov	byte [rsi], '-'
		call	__putc
		pop	rax

.print:		test	rax, rax
		jz	.exit

.skipcheck:	xor	rdx, rdx
		div	rbx
		push	dx
		call	.print
		pop	dx

		mov	byte [rsi], dl
		add	byte [rsi], '0'

		cmp	dl, 10
		jb	.putc
		add	byte [rsi], 'a'-'0'-10

.putc:		call	__putc
.exit:		ret


section .bss

buffer		resb 1
