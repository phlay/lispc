LISPC=../lisp
RUNTIME=../runtime
FLAGS=-c

TESTS=$(patsubst %.lsp,%,$(wildcard test-*.lsp))
FLAGS+=-r $(RUNTIME)

.PHONY: all clean list test
.SUFFIXES: .lsp


all: test

clean:
	@echo "Cleaning up..."
	@for test in $(TESTS); do rm -f $$test; done

list:
	@echo "$(TESTS)"

test: $(TESTS) $(TESTS:test-%=run-%)

test-interpreter: $(TESTS:test-%=interpret-%)


$(TESTS): %: %.lsp common.lsp
	$(LISPC) $(FLAGS) -o $@ $^

run-%: test-%
	@echo "Testing $<..."
	@./$<

interpret-%: test-%.lsp
	@echo "Testing $<..."
	@../lisp $< common.lsp
