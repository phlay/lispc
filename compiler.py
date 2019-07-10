#
# x86_64 native code compiler
#

import os
import subprocess

from lisp import *

class CompileError(LispError): pass



class Compiler:
    def __init__(self, env, target = None):

        self.env = env

        self.recompile(target)


    def recompile(self, target = None):
        self._counter = 0

        self.compiled_lambda = {}

        self.builtin = set()

        self.string_cache = {}
        self.lambda_cache = {}

        if target is None:
            target = [ sym for sym in self.env.symbols if not sym.startswith("_") ]
        elif type(target) != list:
            target = [ target ]

        for sym in target:
            if sym not in self.env.symbols:
                raise CompileError("%s: symbol not found" % (sym))

            item = self.env.symbols[sym]
            if item.is_head("λ"):
                self.lambda_cache[str(item)] = sym
                self.compiled_lambda[sym] = LambdaCompiler(self, item, sym)

    def build(self, output, leave_asm=False):
        asm_name = output + ".asm"
        obj_name = output + ".o"

        # write assembly file
        with open(asm_name, "wb") as f:
            f.write(self.get_assembly().encode('utf8'))

        # try to compile it
        try:
            result = subprocess.run(["nasm", "-f elf64", asm_name, "-o", obj_name], capture_output=True)
            if result.returncode != 0:
                raise CompileError("nasm failed: \n%s" % (result.stderr.decode('utf8')))
        except FileNotFoundError:
            raise CompileError("nasm not found")


        # finally try to link it
        try:
            result = subprocess.run(["ld", "-o", output, obj_name, "runtime/runtime.a" ], capture_output=True)
            if result.returncode != 0:
                raise CompileError("linker failed: \n%s" % (result.stderr.decode('utf8')))

        except FileNotFoundError:
            raise CompileError("ld not found")

        # remove assembler and object file
        try:
            if not leave_asm:
                os.unlink(asm_name)
            os.unlink(obj_name)
        except FileNotFoundError:
            pass    # whatever



    def get_assembly(self):

        result = ""

        result += "extern\tmem_cons\n"
        result += "extern\tmem_int\n"
        result += "extern\tmem_string\n"

        for builtin in self.builtin:
            result += "extern\t%s\n" % (builtin)
            result += "extern\t%s.continue\n" % (builtin)
        result += "\n"

        result += "section .text\n\n"
        for c in self.compiled_lambda.values():
            result += c.text
            result += "\n"

        if self.string_cache:
            result += "section .data\n\n"

            for string, label in self.string_cache.items():
                result += '%s:\tdb "%s"\n' % (label, string)

        return result


    def counter(self):
        result = self._counter
        self._counter += 1
        return result


    def add_lambda(self, expr, label = None):
        # do we have a label for this?
        if str(expr) in self.lambda_cache:
            return self.lambda_cache[str(expr)]

        # anonymous?
        if label is None:
            label = "__lambda_%d" % (self.counter())

        self.lambda_cache[str(expr)] = label
        self.compiled_lambda[label] = LambdaCompiler(self, expr, label)
        return label


    def get_function_label(self, expr):

        if type(expr) == LispSym:
            if expr not in self.env.symbols:
                raise CompileError("%s: undefined symbol" % (expr))

            item = self.env.symbols[expr]
            if type(item) == LispBuiltin:
                self.builtin.add(item.name)
                return item.name, item.argc

            if item.is_head("λ"):
                return self.add_lambda(item, expr), item[1]

            raise CompileError("%s: symbol is not callable" % (expr))

        elif expr.is_head("λ"):
            return self.add_lambda(expr), expr[1]

        raise CompileError("%s: not executeable" % (expr))


    def get_string_label(self, string):
        if string in self.string_cache:
            return self.string_cache[string]

        label = "__string_%d" % (self.counter())
        self.string_cache[string] = label
        return label






class LambdaCompiler:

    REORDER_REGS = ["rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "r14" ]

    def __init__(self, compiler, expr, label):
        self.compiler = compiler

        self.label = label
        self._counter = 0
        self.stack_offset = 0
        self.text = ""

        self.compile(expr)


    def counter(self):
        result = self._counter
        self._counter += 1
        return result


    def compile(self, expr):
        if not expr.is_head("λ"):
            raise CompileError("%s: not a lambda" % (expr))

        lambda_argc = int(expr[1])
        lambda_body = expr[2]

        # emit function label
        if not self.label.startswith("_"):
            self.text += "\tglobal\t%s\n" % (self.label)
            self.text += "\tglobal\t%s.continue\n" % (self.label)
        self.text += "%s:\n" % (self.label)

        # emit prologue
        self.text += "\tpop\trax\n"
        self.text += "\tmov\t[rsp + 8*%d], rax\n" % (lambda_argc)
        self.text += ".continue:\n"

        # emit body
        self.emit_continue_expr(lambda_argc, lambda_body)


    def emit_parameter_reorder(self, old, new):
        if old == 0:
            return

        if new <= len(self.REORDER_REGS):
            for i in range(new):
                self.text += "\tpop\t%s\n" % (self.REORDER_REGS[i])

            self.text += "\tadd\trsp, 8*%d\n" % (old)

            for i in range(new):
                self.text += "\tpush\t%s\n" % (self.REORDER_REGS[new - i - 1])

        else:
            self.text += "\tmov\tecx, %d\n" % (new)
            self.text += "\tlea\trsi, [rsp + 8*%d]\n" % (new - 1)
            self.text += "\tlea\trdi, [rsp + 8*%d]\n" % (old + new - 1)
            self.text += "\tstd\n"
            self.text += "\trep\tmovsq\n"
            self.text += "\tadd\trsp, 8*%d\n" % (old)



    def emit_continue_expr(self, argc, expr):
        if expr.is_atom():
            if type(expr) == LispRef:
                self.text += "\tmov\trax, [rsp + 8*%d]\t; %s\n" % (self.stack_offset + int(expr) - 1,
                                                                   expr)
                self.emit_parameter_reorder(argc, 0)
                self.text += "\tret\n"
            else:
                self.emit_parameter_reorder(argc, 0)
                self.emit_constant_to_rax(expr, exit = True)

            return

        function = expr[0]
        parameter = expr[1:]

        if type(function) == LispSym:

            if function == "if":
                iflabel = ".if_%d_false" % self.counter()

                # evaluate if-expression
                self.text += '\t; evaluate if-condition "%s"\n' % (parameter[0])
                self.emit_call_expr(parameter[0])
                self.text += "\tcall\tcell_is_true\n"
                self.text += "\tjc\t%s\n" % (iflabel)

                # true case
                self.text += "\n"
                self.emit_continue_expr(argc, parameter[1])

                # false case
                self.text += "\n"
                self.text += "%s:\n" % (iflabel)
                self.emit_continue_expr(argc, parameter[2])
                return

            elif function == "λ":
                # XXX
                raise CompileError("can't yet return closures")

            elif function == "quote":
                # XXX
                raise CompileError("can't return quotes yet")


        function_label, function_argc = self.compiler.get_function_label(function)

        # check if number of parameters are correct
        if function_argc is not None and function_argc != len(parameter):
            raise CompileError("%s: exects %d parameter" % (function, function_argc))

        original_parameter_count = len(parameter)       # XXX

        # check for parameter-takeover case
        while argc > 0 and len(parameter) > 0:
            first = parameter[0]
            if type(first) != LispRef or int(first) != argc:
                break

            argc -= 1
            parameter = parameter[1:]

        # now evaluate parameters and push them on stack
        for p in parameter:
            self.emit_call_expr(p)
            self.text += "\tpush\trax\n"
            self.stack_offset += 1
            self.text += "\n"

        # parameter count if needed XXX this has to go!
        if function_argc is None:
            self.text += "\tpush\tqword %d\n" % (original_parameter_count)

        self.emit_parameter_reorder(argc, len(parameter))
        self.stack_offset = 0

        self.text += "\tjmp\t%s.continue\n" % (function_label)


    def emit_call_expr(self, expr):

        if expr.is_atom():
            self.emit_constant_to_rax(expr)
            return

        function = expr[0]
        parameter = expr[1:]

        if type(function) == LispSym:
            if function == "if":
                iflabel = ".if_%d_" % self.counter()
                # evaluate if-expression
                self.text += '\t; evaluate if-condition "%s"\n' % (parameter[0])
                self.emit_call_expr(parameter[0])
                self.text += "\tcall\tcell_is_true\n"
                self.text += "\tjc\t%s\n" % (iflabel+"false")
                # true case
                self.text += "\n"
                self.emit_call_expr(parameter[1])
                self.text += "\tjmp\t%s\n" % (iflabel + "end")
                # false case
                self.text += "\n"
                self.text += "%s:\n" % (iflabel + "false")
                self.emit_call_expr(parameter[2])
                # end if
                self.text += "\n"
                self.text += "%s:\n" % (iflabel + "end")
                return

            elif function == "quote":
                # XXX
                raise CompileError("quote not implemented yet")

        function_label, function_argc = self.compiler.get_function_label(function)
        if function_argc is not None and function_argc != len(parameter):
            raise CompileError("%s: exects %d parameter" % (function, function_argc))

        self.text += "\t; calculate %s\n" % (expr)
        self.text += "\tpush\trax\t\t\t; dummy\n"
        self.stack_offset += 1
        for p in parameter:
            self.emit_call_expr(p)
            self.text += "\tpush\trax\n"
            self.stack_offset += 1

        # parameter count if needed XXX this has to go
        if function_argc is None:
            self.text += "\tpush\tqword %d\n" % (len(parameter))

        self.text += "\tcall\t%s\n" % (function_label)
        self.stack_offset -= len(parameter) + 1



    def emit_constant_to_rax(self, expr, exit = False):

        action = "jmp" if exit else "call"

        if type(expr) == LispInt:
            self.text += "\tmov\trax, %d\n" % (expr)
            self.text += "\t%s\tmem_int\n" % (action)

        #elif type(expr) == LispReal:
        #    self.text += "\tmov\txmm0, %f\n" % (expr)
        #    self.text += "\t%s\tmem_real\n" % (action)

        elif type(expr) == LispRef:
            self.text += "\tmov\trax, [rsp + 8*%d]\t; %s\n" % (self.stack_offset + int(expr) - 1,
                                                               expr)
            if exit:
                raise CompileError("internal error - exit to rax with stack reference")

        #elif type(expr) == LispSym:
        #    label = self.compiler.get_string_label(expr)
        #
        #    self.text += "\tlea\trdi, [%s]\n" % (label)
        #    self.text += "\t%s\tmem_sym\n" % (action)

        elif type(expr) == LispStr:
            label = self.compiler.get_string_label(expr)

            self.text += "\tmov\trsi, %s\n" % (label)
            self.text += "\tmov\trbx, %d\n" % (len(expr))
            self.text += "\t%s\tmem_string\n" % (action)

        elif type(expr) == LispList:
            if len(expr) == 0:
                self.text += "\txor\trax, rax\n"
            else:
                raise CompileError("return of non empty lists are not yet supported")

            if exit:
                self.text += "\tret\n"

        else:
            raise CompileError("can't compile atom: %s" % (expr))

        # XXX emit constant lists

