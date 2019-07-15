%include "runtime.inc"
%include "mem.inc"

		global	__builtin_cons
		global	__builtin_cons.continue

__builtin_cons:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	pop	rbx
		pop	rax

		; fallthrough

;
; construct a new cell from two cell addresses
;
; input:
;	RAX	cell x
;	RBX	cell y
;
; output:
;	RAX	( cons x y )
;
		global	__cons

__cons:		call	__mem_alloc		; allocate cell

		mov	[rdi], rax		; left
		mov	[rdi + 8], rbx		; right

		mov	al, TYPE_CONS		; mark address with info
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		ret
