%include "runtime.inc"

section .text

;
; checks if input is true
;
; input:
;	RAX	input cell
;
; output:
;	CF	true iff CF=0
;
		global	__true

__true:		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		cmp	dl, TYPE_TRUE		; check for 'true' symbol
		je	.true
		test	rax, rbp		; otherwise NIL means false
		jz	.false
.true:		clc				; everthing else is true again
		ret
.false:		stc
		ret
