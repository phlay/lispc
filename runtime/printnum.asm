		extern putc

section .text


; printnum10 - print decimal number
;
; rax		number to print
;

		global printnum10

printnum10:	mov	rbx, 10


; printnum - print number using putc
;
; rax		number to print
; rbx		radix with 0 < rbx <= 10
;
; changes: rax (=0), rcx, rdx, rsi, rdi
;
		global printnum

printnum:	mov	rsi, buffer

		; in case of non-negative number go right into recursion
		; but skip the intro check (so zero gets printed).
		test	rax, rax
		jge	.skipcheck

		neg	rax			; make rax positive
		push	rax			; and print minus
		mov	byte [rsi], '-'
		call	putc
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

.putc:		call	putc
.exit:		ret


section .bss

	buffer		resb 1
