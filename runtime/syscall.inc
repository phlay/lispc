;
; see /usr/include/asm/unistd_64.h
;

SYS_READ        equ     0
SYS_WRITE       equ     1
SYS_OPEN        equ     2
SYS_CLOSE       equ     3
SYS_STAT	equ	4
SYS_FSTAT	equ	5
SYS_LSTAT	equ	6
SYS_POLL	equ	7
SYS_LSEEK	equ	8
SYS_MMAP	equ	9
SYS_MPROTECT	equ	10
SYS_MUNMAP	equ	11
SYS_BRK         equ     12
SYS_IOCTL	equ	16

SYS_EXIT        equ     60


;
; file descriptoren
;
FD_STDIN        equ     0
FD_STDOUT       equ     1


;
; mmap
;
PROT_READ	equ	1
PROT_WRITE	equ	2
PROT_EXEC	equ	4

MAP_SHARED	equ	0x01
MAP_PRIVATE	equ	0x02
MAP_ANONYMOUS	equ	0x20

MAP_FAILED	equ	-1
