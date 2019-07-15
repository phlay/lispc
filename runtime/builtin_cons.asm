%include "runtime.inc"
%include "mem.inc"

;
; constructs new cell from two cell addresses
;
; input:
;	stack:	dummy, X, Y
;
; output:
;	RAX	( cons X Y )
;

		global	__builtin_cons
		global	__builtin_cons.continue

__builtin_cons:	pop	rax
		mov	[rsp + 2*8], rax

.continue:	call	__mem_alloc
		pop	qword [rdi + 8]
		pop	qword [rdi]

		mov	al, TYPE_CONS		; mark address with info
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		ret


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

__cons:		push	rbx			; push on stack for GC
		push	rax
		call	__mem_alloc		; allocate cell
		pop	qword [rdi]		; left
		pop	qword [rdi + 8]		; right

		mov	al, TYPE_CONS		; mark address with info
		shl	rax, SHIFT_TYPE
		or	rax, rdi
		ret
