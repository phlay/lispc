AS = nasm
ASFLAGS = -f elf64 #-DDEBUG

OBJ = start.o mem.o panic.o puts.o printnum.o true.o apply.o \
      builtin_cons.o builtin_head.o builtin_tail.o builtin_print.o \
      builtin_atom.o builtin_eval.o builtin_arith.o builtin_bool.o \
      builtin_eq.o builtin_list.o

.PHONY: clean cleanall all
.SUFFIXES: .asm

all:	runtime.a builtin_head.o builtin_tail.o builtin_print.o


clean:
	rm -f *.o

cleanall: clean
	rm -f runtime.a

.asm.o:
	$(AS) $(ASFLAGS) $< -o $@

print-%:
	@echo $*=$($*)

runtime.a: $(OBJ)
	ar rcs $@ $(OBJ)
