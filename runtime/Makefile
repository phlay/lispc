AS = nasm
ASFLAGS = -f elf64

OBJ = start.o mem.o panic.o puts.o putc.o printnum.o true.o call.o \
      builtin_cons.o builtin_head.o builtin_tail.o builtin_print.o \
      builtin_atom.o builtin_quote.o builtin_eval.o

.PHONY: clean distclean all
.SUFFIXES: .asm

all:	runtime.a builtin_head.o builtin_tail.o builtin_print.o


clean:
	rm -f *.o

distclean: clean
	rm -f runtime.a

.asm.o:
	$(AS) $(ASFLAGS) $< -o $@

print-%:
	@echo $*=$($*)

runtime.a: $(OBJ)
	ar rcs $@ $(OBJ)
