%include "runtime.inc"
%include "printnum.inc"
%include "puts.inc"
%include "putc.inc"


section .text


; prints it's parameter in nice form
;
; input:
;	rcx	k
;	stack	dummy, p1, ..., pk
;
; where p1, ..., pk are the cell-addresses to be printed
;

		global	__builtin_print
		global	__builtin_print.continue

__builtin_print:
		pop	rax
		mov	[rsp + 8*rcx], rax

.continue:	mov	r9, rcx			; r9 <- k
		lea	r10, [rsp + 8*r9]	; r10 <- &ret = &p1 + 8
		clc

.loop:		sub	r10, 8
		cmp	r10, rsp
		jb	.done

		mov	r8, [r10]		; r8 <- p_i
		xor	al, al			; no ""
		call	print_cell
		jc	.err
		jmp	.loop

.done:		clc
.err:		lea	rsp, [rsp + 8*r9]	; clear stack
		ret


		global	__builtin_println
		global	__builtin_println.continue

__builtin_println:
		pop	rax
		mov	[rsp + 8*rcx], rax

.continue:	push	msg_nl
		inc	rcx
		jmp	__builtin_print.continue



; print_cell - prints a cell to stdout
;
; input:
;	r8	cell
;	al	true if we should print "" around strings
;
; XXX should set carry in case of error
;
print_cell:	mov	rdx, r8			; dl <- type(r8)
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	r8, rbp			; r8 <- addr(r8)

		;test	dl, dl
		;jz	print_ptr
		test	dl, dl
		jz	print_cstr
		cmp	dl, TYPE_CONS
		je	print_cons
		cmp	dl, TYPE_INT
		je	print_int
		cmp	dl, TYPE_STR
		je	print_string
		cmp	dl, TYPE_LAMBDA
		je	print_lambda

		stc
		ret

;print_ptr:	mov	rsi, msg_hex
;		call	__puts
;		mov	rax, r8
;		mov	rbx, 16
;		call	__printnum
;		clc
;		ret

print_cstr:	mov	rsi, r8
		call	__puts
		clc
		ret

print_cons:	test	r8, r8
		jz	.nil

		mov	rsi, char_lb
		call	__putc
		xor	al, al			; set al to 1 to print
		inc	al			; "" around strings

.left:		push	r8
		mov	r8, [r8]		; r8 <- left(r8)
		call	print_cell
		pop	r8

		mov	r8, [r8 + 8]		; r8 <- right(r8)
		mov	rdx, r8
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		test	r8, rbp			; check for NIL
		jz	.out
		cmp	dl, TYPE_CONS		; check type
		jne	.right
		call	__putsp
		and	r8, rbp
		jmp	.left

.right:		call	__putsp
		mov	rsi, char_dot
		call	__putc
		call	__putsp
		call	print_cell
.out:		mov	rsi, char_rb
		call	__putc
		clc
		ret

.nil:		mov	rsi, msg_nil
		call	__puts
		clc
		ret



print_int:	mov	rax, [r8]		; rax <- left(r8)
		call	__printnum10
		clc
		ret

print_string:	test	al, al
		jz	.start

		mov	rsi, char_dq
		call	__putc
		call	.start
		jc	.out
		mov	rsi, char_dq
		call	__putc
.done:		clc
.out:		ret

.start:		test	r8, r8			; empty string?
		jz	.done

		mov	rsi, r8
		mov	rcx, 8

.loop:		cmp	byte [rsi], 0
		je	.done
		push	rcx
		call	__putc
		pop	rcx
		inc	rsi
		loop	.loop

		mov	r8, [r8 + 8]
		mov	rdx, r8
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	r8, rbp
		jz	.done
		cmp	dl, TYPE_STR
		jne	.error
		jmp	.start

.error:		mov	rsi, msg_strerror	; XXX
		call	__puts
		stc
		ret

print_lambda:	mov	rsi, msg_lambda
		call	__puts

		mov	rax, [r8 + 8]
		and	rax, rbp
		call	__printnum10
		call	__putsp

		lea	rsi, [msg_hex]
		call	__puts

		mov	rax, [r8]
		mov	rbx, 16
		call	__printnum

		lea	rsi, [char_rb]
		call	__putc

		clc
		ret


section .data

msg_strerror	db "<string error>", 0
msg_hex		db "0x", 0
msg_lambda	db "(λ ", 0
msg_nl		db `\n`, 0
msg_nil		db "NIL", 0
char_lb		db '('
char_rb		db ')'
char_dot	db '.'
char_dq		db '"'
