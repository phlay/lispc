%include "runtime.inc"
%include "printnum.inc"
%include "puts.inc"
%include "panic.inc"


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

.loop:		sub	r10, 8
		cmp	r10, rsp
		jb	.done

		mov	r8, [r10]		; r8 <- p_i
		xor	al, al			; no ""
		call	__print_cell
		jmp	.loop

.done:		lea	rsp, [rsp + 8*r9]	; clear stack
		ret


		global	__builtin_println
		global	__builtin_println.continue

__builtin_println:
		pop	rax
		mov	[rsp + 8*rcx], rax

.continue:	push	msg_nl
		inc	rcx
		jmp	__builtin_print.continue



;
; prints a cell to stdout
;
; input:
;	r8	cell
;	al	true if we should print "" around strings
;
;
		global	__print_cell
__print_cell:
		mov	rdx, r8			; dl <- type(r8)
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	r8, rbp			; r8 <- addr(r8)

		;test	dl, dl
		;jz	print_ptr
		cmp	dl, TYPE_STR		; print types with special
		je	print_string		; NILs first
		cmp	dl, TYPE_TRUE
		je	print_true
		cmp	dl, TYPE_QUOTE
		je	print_quote

		test	r8, r8			; now handle NIL
		jz	print_nil
		test	dl, dl			; print-str after NIL check
		jz	print_cstr

		cmp	dl, TYPE_CONS
		je	print_cons
		cmp	dl, TYPE_INT
		je	print_int
		cmp	dl, TYPE_LAMBDA
		je	print_lambda
		cmp	dl, TYPE_CLOSURE
		je	print_closure

		jmp	__panic_type

;print_ptr:	lea	rsi, [msg_hex]
;		call	__puts
;		mov	rax, r8
;		mov	rbx, 16
;		call	__printnum
;		ret

print_cstr:	mov	rsi, r8
		call	__puts
		ret

print_true:	lea	rsi, [msg_true]
		call	__puts
		ret

print_quote:	lea	rsi, [msg_quote]
		call	__puts
		ret


print_nil:	lea	rsi, [msg_nil]
		call	__puts
		ret

print_cons:	lea	rsi, [char_lb]
		call	__putc
		xor	al, al			; set al to 1 to print
		inc	al			; "" around strings

.left:		push	r8
		mov	r8, [r8]		; r8 <- left(r8)
		call	__print_cell
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
		lea	rsi, [char_dot]
		call	__putc
		call	__putsp
		call	__print_cell
.out:		lea	rsi, [char_rb]
		call	__putc
		ret


print_int:	mov	rax, [r8]		; rax <- left(r8)
		call	__printnum10
		ret

print_string:	test	al, al
		jz	.start

		lea	rsi, [char_dq]
		call	__putc
		call	.start
		lea	rsi, [char_dq]
		call	__putc
.done:		ret

.start:		test	r8, r8			; empty string?
		jz	.done

.print_block:	mov	rsi, r8
		mov	rcx, 8

.print_char:	cmp	byte [rsi], 0
		je	.done
		push	rcx
		call	__putc
		pop	rcx
		inc	rsi
		loop	.print_char

		mov	r8, [r8 + 8]
		mov	rdx, r8
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	r8, rbp
		jz	.done
		cmp	dl, TYPE_STR
		jne	__panic_type
		jmp	.print_block


print_lambda:	lea	rsi, [msg_lambda]
		call	__puts

.continue:
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
		ret

print_closure:	lea	rsi, [msg_closure]
		call	__puts

		push	qword [r8]		; save pointer to lambda
		mov	r8, [r8 + 8]		; print captured stack
		call	__print_cell
		call	__putsp

		pop	r8			; restore lambda
		and	r8, rbp			; no type check
		jmp	print_lambda.continue


section .data

msg_hex		db "0x", 0
msg_closure	db "(ξ ", 0
msg_lambda	db "(λ ", 0
msg_nl		db `\n`, 0
msg_nil		db "#NIL", 0
msg_true	db "#T", 0
msg_quote	db "quote", 0
char_lb		db '('
char_rb		db ')'
char_dot	db '.'
char_dq		db '"'
