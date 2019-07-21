%include "runtime.inc"
%include "syscall.inc"
%include "puts.inc"
%include "printnum.inc"
%include "start.inc"


section	.text


		global	__panic_memory
__panic_memory:	lea	rsi, [panic_memory]
		jmp	exit_with_msg


		global	__panic_oom
__panic_oom:	lea	rsi, [panic_oom]
		jmp	exit_with_msg


;
; unexected type is given in dl
;
		global	__panic_type
__panic_type:	push	rdx
		lea	rsi, [panic_type]
		call	print_error_msg
		pop	rdx
		xor	rax, rax
		mov	al, dl
		call	__printnum10
		call	__putnl
		jmp	exit_with_trace



		global	__panic_nil
__panic_nil:	lea	rsi, [panic_nil]
		jmp	exit_with_msg_trace


		global	__panic_overflow
__panic_overflow:
		lea	rsi, [panic_overflow]
		jmp	exit_with_msg_trace


		global	__panic_underflow
__panic_underflow:
		lea	rsi, [panic_underflow]
		jmp	exit_with_msg_trace


		global	__panic_argc
__panic_argc:
		lea	rsi, [panic_argc]
		jmp	exit_with_msg_trace


		global	__panic_notyet
__panic_notyet:
		lea	rsi, [panic_notyet]
		jmp	exit_with_msg_trace


;
; helper function that displays 'Error: <msg>\n'
;
; input:
;	RSI	msg
;
print_error_msg:
		push	rsi
		lea	rsi, [msg_error]
		call	__puts
		pop	rsi
		call	__puts
		ret


;
; display message and exit with error level 1
;
; input:
;	RSI	error message to display
;
exit_with_msg:
		call	print_error_msg
		call	__putnl

exit:		mov	rax, SYS_EXIT
		xor	rdi, rdi
		inc	rdi
		syscall



;
; dispays stacktrace and exits with error level 1
;
;
exit_with_trace:
		lea	rsi, [msg_stacktrace]
		call	__puts

.loop:		cmp	rsp, [__start_stack]
		jae	exit

		pop	rax
		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		test	dl, BYTEMASK_TYPE
		jnz	.loop

		push	rax
		lea	rsi, [msg_hex]
		call	__puts
		pop	rax
		mov	rbx, 16
		call	__printnum
		call	__putnl
		jmp	.loop

; XXX while cool this is very dangerous!
;.print_cell:	mov	r8, rax
;		mov	al, 1
;		call	__print_cell
;		call	__putnl
;		jmp	.loop

;
; first displayes a message and than a stacktrace,
; finally exits with error level 1
;
; input:
;	RSI	message to print
;
exit_with_msg_trace:
		call	print_error_msg
		jmp	exit_with_trace




section .data

msg_error		db `Error: `, 0
msg_stacktrace		db `\nStacktrace:\n`, 0
msg_hex			db ` > 0x`, 0

panic_memory		db `memory initialization failed`, 0
panic_oom		db `out of memory`, 0
panic_type		db `illegal type: `, 0
panic_nil		db `unexpected #NIL`, 0
panic_overflow		db `overflow`, 0
panic_underflow		db `underflow`, 0
panic_argc		db `illegal number of parameter`, 0
panic_notyet		db `feature not yet implemented`, 0
