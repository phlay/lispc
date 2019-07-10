%include "printnum.inc"
%include "puts.inc"
%include "putc.inc"
%include "cell.inc"


section .text


; prints it's parameter in nice form
;
; stack: dummy, p1, ..., pk, k
;
; where p1, ..., pk are the cell-addresses to be printed
;

		global	__builtin_print
		global	__builtin_print.continue

__builtin_print:
		pop	rax			; extended prologue
		pop	rbx
		mov	[rsp + 8*rbx], rax
		push	rbx

.continue:	pop	r9			; r9 <- k
		lea	r10, [rsp + 8*r9]	; r10 <- &ret = &p1 + 8
		clc

.loop:		sub	r10, 8
		cmp	r10, rsp
		jb	.done

		mov	r8, [r10]		; r8 <- p_i
		call	print_cell
		jc	.err
		jmp	.loop

.done:		clc
.err:		lea	rsp, [rsp + 8*r9]	; clear stack
		ret


		global	__builtin_println
		global	__builtin_println.continue

__builtin_println:
		pop	rax			; extended prologue
		pop	rbx
		mov	[rsp + 8*rbx], rax
		push	rbx

.continue:	pop	rbx
		inc	rbx
		push	msg_nl
		push	rbx
		jmp	__builtin_print.continue



; print_cell - prints a cell to stdout
;
; input:
;	r8	cell
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
		test	r8, r8
		jz	print_nil
		cmp	dl, TYPE_CONS
		je	print_cons
		cmp	dl, TYPE_INT
		je	print_int
		cmp	dl, TYPE_STR
		je	print_str

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

print_nil:	mov	rsi, msg_nil
		call	__puts
		clc
		ret

print_cons:	mov	rsi, char_lb
		call	__putc

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

print_int:	mov	rax, [r8]		; rax <- left(r8)
		call	__printnum10
		clc
		ret

print_str:	mov	rsi, r8
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
		jmp	print_str

.done:		clc
		ret

.error:		mov	rsi, msg_strerror
		call	__puts
		stc
		ret



section .data

msg_strerror	db "<string error>", 0
msg_hex		db "0x", 0
msg_nl		db `\n`, 0
msg_nil		db "NIL", 0
char_lb		db '('
char_rb		db ')'
char_dot	db '.'
