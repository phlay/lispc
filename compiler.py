#
# x86_64 native code compiler
#

import os
import subprocess

from lisp import *

class CompileError(LispError): pass



class Compiler:

    def __init__(self, env):
        self.env = env
        self.target_symbol = "main"
        self.runtime_path = None
        self.leave_asm_file = False

        self.reset()


    def set_target_symbol(self, target):
        self.target_symbol = target

    def set_runtime(self, path):
        self.runtime_path = path

    def set_leave_asm(self, leave):
        self.leave_asm_file = leave

    def reset(self):
        self.extern = set()
        self.compiled_lambda = {}
        self.string_cache = {}
        self.lambda_cache = {}
        self.counter = 0


    def compile(self, sym):
        if sym not in self.env.symbols:
            raise CompileError("%s: symbol not found" % (sym))

        item = self.env.symbols[sym]
        if item.is_head("λ"):
            self.lambda_cache[str(item)] = sym
            self.compiled_lambda[sym] = LambdaCompiler(self, item, sym)
        else:
            raise CompileError("%s: not a function" % (sym))


    def get_assembly(self):

        self.reset()
        self.compile(self.target_symbol)

        result = ""

        for label in self.extern:
            result += "extern\t%s\n" % (label)
        result += "\n"


        result += "section .text\n\n"
        for c in self.compiled_lambda.values():
            result += c.text
            result += "\n\n"

        if self.string_cache:
            result += "section .data\n\n"

            for string, label in self.string_cache.items():
                result += '%s:\tdb "%s"\n' % (label, string)

        return result


    def build(self, output):
        runtime_path = os.path.expanduser(self.runtime_path) + "/"
        runtime_file = runtime_path + "runtime.a"
        asm_file = output + ".asm"
        obj_file = output + ".o"

        # write assembly file
        with open(asm_file, "wb") as f:
            f.write(self.get_assembly().encode('utf8'))

        # try to compile it
        try:
            result = subprocess.run(["nasm",
                                     "-o", obj_file,
                                     "-f elf64",
                                     "-I", runtime_path,
                                     "-p runtime.inc",
                                     asm_file], capture_output=True)

            if result.returncode != 0:
                raise CompileError("nasm failed: %s" %
                        (result.stderr.decode('utf8')))

        except FileNotFoundError:
            raise CompileError("nasm not found")


        # finally try to link it
        try:
            result = subprocess.run(["ld",
                                     "-o", output,
                                     obj_file,
                                     runtime_file ], capture_output=True)

            if result.returncode != 0:
                raise CompileError("linker failed: \n%s" %
                        (result.stderr.decode('utf8')))

        except FileNotFoundError:
            raise CompileError("ld not found")

        # remove assembler and object file
        try:
            if not self.leave_asm_file:
                os.unlink(asm_file)
            os.unlink(obj_file)
        except FileNotFoundError:
            pass    # whatever



    def get_unique(self):
        result = "%06d" % self.counter
        self.counter += 1
        return result


    def get_function_label(self, expr, sym = None):

        # do we get an symbol? resolve it
        while type(expr) == LispSym:
            sym = expr
            if sym not in self.env.symbols:
                raise CompileError("%s: undefined symbol" % (sym))

            expr = self.env.symbols[sym]

        if expr.is_head("λ"):
            argc = expr[1]

            # do we already have a label for this?
            if str(expr) in self.lambda_cache:
                return self.lambda_cache[str(expr)], argc

            # invent a label if this is anonymous
            if sym is None:
                label = "__lambda_%s" % (self.get_unique())
            else:
                label = sym

            # finally enter laber in our cache and compile it
            self.lambda_cache[str(expr)] = label
            self.compiled_lambda[label] = LambdaCompiler(self, expr, label)

            return label, argc

        elif type(expr) == LispBuiltin:
            self.extern.add(expr.extern)
            self.extern.add(expr.extern + ".continue")

            return expr.extern, expr.argc


        raise CompileError("%s: not executeable" % (expr))



    def get_string_label(self, string):
        if string in self.string_cache:
            return self.string_cache[string]

        label = "__string_%s" % (self.get_unique())
        self.string_cache[string] = label
        return label





class LambdaCompiler:

    REORDER_REGS = [ "rbx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "r14" ]

    def __init__(self, compiler, expr, label):
        self.compiler = compiler

        self.label = label
        self.counter = 0
        self.stack_offset = 0
        self.text = ""

        self.compile(expr)


    def get_unique(self):
        result = "%06d" % self.counter
        self.counter += 1
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
                self.text += "\tmov\trax, [rsp + 8*%d]\t; %s\n" % \
                        (self.stack_offset + int(expr) - 1, expr)
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
                self.compiler.extern.add("__true")
                iflabel = ".if_%s_false" % self.get_unique()
                # evaluate if-expression
                self.text += '\t; evaluate if-condition "%s"\n' % (parameter[0])
                self.emit_call_expr(parameter[0])
                self.text += "\tcall\t__true\n"
                self.text += "\tjc\t%s\n" % (iflabel)
                # true case
                self.text += "\n"
                self.emit_continue_expr(argc, parameter[1])
                # false case
                self.text += "\n"
                self.text += "%s:\n" % (iflabel)
                self.emit_continue_expr(argc, parameter[2])
                return

            elif function == "eval":
                self.compiler.extern.add("__eval")
                self.emit_call_expr(parameter[0])
                self.text += "\tjmp\t__eval\n"
                return

            elif function == "quote":
                self.emit_continue_expr(parameter[0].consify())
                return

            elif function == "λ":
                # XXX
                raise CompileError("can't yet return closures")

        #
        # check for parameter-takeover case: function we call
        # directly uses our parameters on stack.
        # parameter_count still holds the original number of
        # parameter the function gets.
        #
        parameter_count = len(parameter)
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

        #
        # now we call our function, there are two cases
        #
        #  1) Dynamic Function, given by a local reference
        #  2) Static Funcion, either by symbol or explicitly by lambda
        #
        if type(function) == LispRef:
            self.text += "\tmov\trax, [rsp + 8*%d]\n" % \
                    (self.stack_offset + int(function) - 1)
            self.emit_parameter_reorder(argc, len(parameter))
            self.text += "\tmov\trcx, %d\n" % (parameter_count)
            self.text += "\tjmp\t__call.continue\n"
            self.compiler.extern.add("__call.continue")

        else:
            function_label, function_argc = self.compiler.get_function_label(function)
            if function_argc is not None and function_argc != parameter_count:
                raise CompileError("%s: expects %d parameter but got %d"
                        % (function, function_argc, parameter_count))

            self.emit_parameter_reorder(argc, len(parameter))

            # if variadic, inform our function how many parameter it is receiving
            if function_argc is None:
                self.text += "\tmov\trcx, %d\n" % (parameter_count)

            self.text += "\tjmp\t%s.continue\n" % (function_label)

        self.stack_offset -= len(parameter)



    def emit_call_expr(self, expr):

        #print("[DEBUG] emit_call_expr: %s" % (expr))

        if expr.is_atom():
            self.emit_constant_to_rax(expr)
            return

        function = expr[0]
        parameter = expr[1:]

        if type(function) == LispSym:
            if function == "if":
                self.compiler.extern.add("__true")
                iflabel = ".if_%s_" % self.get_unique()
                # evaluate if-condition
                self.text += '\t; evaluate if-condition "%s"\n' % (parameter[0])
                self.emit_call_expr(parameter[0])
                self.text += "\tcall\t__true\n"
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

            elif function == "eval":
                self.compiler.extern.add("__eval")
                self.emit_call_expr(parameter[0])
                self.text += "\tcall\t__eval\n"
                return

            elif function == "quote":
                self.emit_call_expr(parameter[0].consify())
                return

        # push parameter for function call
        self.text += "\t; calculate %s\n" % (expr)
        self.text += "\tpush\trax\t\t\t; dummy\n"
        self.stack_offset += 1
        for p in parameter:
            self.emit_call_expr(p)
            self.text += "\tpush\trax\n"
            self.stack_offset += 1

        #
        # Like above, we can have dynamic or static functions
        #
        if type(function) == LispRef:
            self.text += "\tmov\trax, [rsp + 8*%d]\n" % \
                    (self.stack_offset + int(function) - 1)
            self.text += "\tmov\trcx, %d\n" % (len(parameter))
            self.text += "\tcall\t__call\n"
            self.compiler.extern.add("__call")

        else:
            function_label, function_argc = self.compiler.get_function_label(function)
            if function_argc is not None and function_argc != len(parameter):
                raise CompileError("%s: expects %d parameter but got %d" %
                        (function, function_argc, len(parameter)))

            # parameter count if called function is variadic
            if function_argc is None:
                self.text += "\tmov\trcx, %d\n" % (len(parameter))

            self.text += "\tcall\t%s\n" % (function_label)

        self.stack_offset -= len(parameter) + 1



    def emit_constant_to_rax(self, expr, exit = False):

        action = "jmp" if exit else "call"
        sym = None

        # if expression is a symbol, we resolve it first
        if type(expr) == LispSym:
            sym = expr
            if sym not in self.compiler.env.symbols:
                raise CompileError("%s: undefined symbol" % (sym))

            expr = self.compiler.env.symbols[sym]


        if type(expr) == LispInt:
            self.compiler.extern.add("__mem_int")
            self.text += "\tmov\trax, %d\n" % (expr)
            self.text += "\t%s\t__mem_int\n" % (action)

        #elif type(expr) == LispReal:
        #    self.text += "\tmov\txmm0, %f\n" % (expr)
        #    self.text += "\t%s\t__mem_real\n" % (action)

        elif type(expr) == LispRef:
            self.text += "\tmov\trax, [rsp + 8*%d]\t; %s\n" % \
                    (self.stack_offset + int(expr) - 1, expr)
            if exit:
                raise CompileError("internal error - exit to rax with stack reference")

        elif type(expr) == LispTrue:
            self.text += "\tmov\tal, TYPE_TRUE\n"
            self.text += "\tshl\trax, SHIFT_TYPE\n"
            if exit:
                self.text += "\tret\n"

        elif type(expr) == LispStr:
            self.compiler.extern.add("__mem_string")
            label = self.compiler.get_string_label(expr)

            self.text += "\tmov\trsi, %s\n" % (label)
            self.text += "\tmov\trbx, %d\n" % (len(expr))
            self.text += "\t%s\t__mem_string\n" % (action)

        elif type(expr) == LispBuiltin or expr.is_head("λ"):
            function_label, function_argc = self.compiler.get_function_label(expr, sym)

            self.text += "\tlea\trsi, [%s.continue]\n" % (function_label)
            if function_argc is None:
                self.text += "\tmov\trbx, LAMBDA_VARIADIC\n"
            elif function_argc == 0:
                self.text += "\txor\trbx, rbx\n"
            else:
                self.text += "\tmov\trbx, %d\n" % (function_argc)

            self.compiler.extern.add("__mem_lambda")
            self.text += "\t%s\t__mem_lambda\n" % (action)

        elif type(expr) == LispList:
            if len(expr) == 0:
                self.text += "\txor\trax, rax\n"
                if exit:
                    self.text += "\tret\n"
            else:
                if exit:
                    self.emit_continue_expr(expr.consify())
                else:
                    self.emit_call_expr(expr.consify())

        else:
            raise CompileError("can't compile atom: %s" % (expr))
