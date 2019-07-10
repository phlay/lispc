AS = nasm
ASFLAGS = -f elf64

OBJ = start.o mem.o panic.o puts.o putc.o printnum.o builtin_head.o builtin_tail.o builtin_print.o

.PHONY: clean all
.SUFFIXES: .asm

all:	runtime.a builtin_head.o builtin_tail.o builtin_print.o


clean:
	rm -f *.o runtime.a

.asm.o:
	$(AS) $(ASFLAGS) $< -o $@

print-%:
	@echo $*=$($*)


runtime.a: $(OBJ)
	ar rcs $@ $(OBJ)

