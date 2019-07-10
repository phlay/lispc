%include "cell.inc"

;
; checks if input cell is true
;
; input:
;	RAX	input cell
;
; output:
;
;	true  := carry flag clear
;	false := carry flag set
;
		global	__true

__true:		mov	rdx, rax
		shr	rdx, SHIFT_TYPE
		and	dl, BYTEMASK_TYPE
		and	rax, rbp
		jz	.false

		cmp	dl, TYPE_INT
		jne	.true			; all other types are 'true'

		;; we have an int, check it
		mov	rbx, [rax]
		test	rbx, rbx
		jz	.false

.true:		clc
		ret
.false:		stc
		ret
