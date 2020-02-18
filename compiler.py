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
        self.lambda_cache = {}
        self.string_cache = {}
        self.capture_cache = {}
        self.counter = 0


    def compile_symbol(self, sym):
        if sym not in self.env.symbols:
            raise CompileError("%s: symbol not found" % (sym))

        item = self.env.symbols[sym]

        if type(item) == LispClosure:
            item = item.resolve()

        return self.compile_expression(item, sym)


    def compile_expression(self, expr, name=None):
        if isinstance(expr, LispLambda):
            # do we already have a label for this?
            if str(expr) in self.lambda_cache:
                return self.lambda_cache[str(expr)], expr.argc

            # invent a label if this is anonymous
            if name is None:
                label = "__lambda_%s" % (self.get_unique())
            else:
                label = name

            # finally enter laber in our cache and compile it
            self.lambda_cache[str(expr)] = label
            self.compiled_lambda[label] = LambdaCompiler(self, expr, label)

            return label, expr.argc

        elif type(expr) == LispBuiltin:
            self.extern.add(expr.extern)
            self.extern.add(expr.extern + ".continue")

            return expr.extern, expr.argc


        raise CompileError("%s: not executable" % (expr))




    def get_assembly(self):

        self.reset()
        self.compile_symbol(self.target_symbol)

        result = ""

        for label in self.extern:
            result += "extern\t%s\n" % (label)
        result += "\n"


        result += "section .text\n\n"
        for c in self.compiled_lambda.values():
            result += c.text
            result += "\n\n"

        if self.string_cache or self.capture_cache:
            result += "section .data\n\n"

            for string, label in self.string_cache.items():
                result += '%s\tdb "%s"\n' % (label, string)

            for capture, label in self.capture_cache.items():
                result += '%s\tdw %s, 0\n' % (label, capture)


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



    def get_string_label(self, string):
        if string in self.string_cache:
            return self.string_cache[string]

        label = "__string_%s" % (self.get_unique())
        self.string_cache[string] = label
        return label

    def get_capture_label(self, capture):
        key = ', '.join([ str(8*i) for i in reversed(capture) ])

        if key in self.capture_cache:
            return self.capture_cache[key]

        label = "__capture_%s" % (self.get_unique())
        self.capture_cache[key] = label
        return label



class LambdaCompiler:

    REORDER_REGS = [ "rbx", "rcx", "rdx", "rsi", "rdi", "r8",
                     "r9", "r10", "r11", "r12", "r13", "r14" ]


    def __init__(self, compiler, expr, label):
        self.compiler = compiler

        self.label = label
        self.counter = 0
        self.text = ""

        self.compile(expr)


    def get_unique(self):
        result = "%06d" % self.counter
        self.counter += 1
        return result


    def compile(self, expr):
        if not isinstance(expr, LispLambda):
            raise CompileError("%s: not a lambda" % (expr))

        lambda_body = expr.body
        lambda_bindings = expr.argc
        if type(expr) == LispClosure:
            lambda_bindings += len(expr.capture_indices)

        # emit function label
        if not self.label.startswith("_"):
            self.text += "\tglobal\t%s\n" % (self.label)
            self.text += "\tglobal\t%s.continue\n" % (self.label)
        self.text += "%s:\n" % (self.label)

        # emit prologue
        self.text += "\tpop\trax\n"
        self.text += "\tmov\t[rsp + 8*%d], rax\n" % (lambda_bindings)
        self.text += ".continue:\n"

        # emit body
        self.emit_expression(lambda_body, lambda_bindings, final=True)



    def emit_stack_reorder(self, old, new=0):
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


    #
    # emit_expression - recursively compile expression
    #
    # bindings      The number of variables on stack we are responsible for:
    #               All bindings must be cleaned up after the call or for
    #               jumping.
    #
    # offset        Offset for local references: everytime we change the stack
    #               this must be adjusted. If we execute a new body we can set
    #               reset back to 0.
    #
    # final         True if this is the last expression in lambda.
    #
    def emit_expression(self, expr, bindings=0, offset=0, final=False):
        #print("[DEBUG] emit_expression: %s" % (expr))
        #print("[DEBUG] \t\t bindings=%d, offset=%d, final=%s" % (bindings, offset, final))

        if expr.is_atom():
            self.emit_constant(expr, bindings=bindings,
                                     offset=offset,
                                     final=final)
            return

        function = expr[0]
        parameter = expr[1:]

        if type(function) == LispSym:
            if function == "if":
                self.compiler.extern.add("__true")
                iflabel = ".if_%s_" % self.get_unique()

                # evaluate if-expression
                #self.text += '\t; evaluate if-condition "%s"\n' % (parameter[0])
                self.emit_expression(parameter[0], offset=offset)
                self.text += "\tcall\t__true\n"
                self.text += "\tjc\t%s\n" % (iflabel + "false")

                #
                # now emit true and false branches for our if
                #
                # we push responsibility for our bindings to next level and let
                # it do the cleanup (even if final is False).
                #

                # true case
                self.text += "\n"
                self.emit_expression(parameter[1], bindings, offset, final)
                if not final:
                    self.text += "\tjmp\t%s\n" % (iflabel + "end")

                # false case
                self.text += "\n"
                self.text += "%s:\n" % (iflabel + "false")
                self.emit_expression(parameter[2], bindings, offset, final)

                # add end-label if we aren't  a final expression
                if not final:
                    self.text += "\n"
                    self.text += "%s:\n" % (iflabel + "end")
                return

            elif function == "eval":
                self.compiler.extern.add("__eval")
                self.emit_expression(parameter[0], offset=offset)
                self.text += "\t%s\t__eval\n" % ("jmp" if final else "call")
                return

            elif function == "quote":
                self.emit_constant(parameter[0], bindings=bindings,
                                                 offset=offset,
                                                 final=final)
                return



        # Save the original number of parameter. Code below might change
        # parameter array (for parameter take-over), but we still need
        # the original length in some places.
        parameter_count = len(parameter)


        if final:
            # check for parameter take-over optimization: If we continue (jump)
            # to a function which uses exactly the same parameter we ourself
            # got (and maybe additional ones) we can save ourself the work
            # for re-pushing and later stack-reordering.
            # don't do this in case we use a lambda to introduce new bindings.
            if type(function) != LispLambda:
                while bindings > 0 and len(parameter) > 0:
                    first = parameter[0]
                    if type(first) != LispRef or int(first) != bindings:
                        break

                    # remove from bindings, to exclude it from stack-reorder
                    bindings -= 1
                    # remove from parameter list: it is already on our stack
                    parameter = parameter[1:]
        else:
            # if this is not a local binding we are going to call a function
            # and therefor need a dummy on our stack
            self.text += "\t; %s\n" % (expr)
            if type(function) != LispLambda:
                self.text += "\tpush\trax\t\t\t; dummy\n"
                offset += 1


        #
        # now evaluate parameters and push them on stack
        #
        for p in parameter:
            self.emit_expression(p, offset=offset)
            self.text += "\tpush\trax\n"
            offset += 1
            self.text += "\n"


        #
        # now we call or continue to our function, there are three cases
        #
        #  1) Dynamic Function, given by a local reference
        #  2) Dynamic Function, given as result of a lambda application
        #  3) Local Binding, a call to an anonymous lambda
        #  4) Static Function, a lambda call given by symbol
        #
        if type(function) == LispRef:
            self.text += "\tmov\trax, [rsp + 8*%d]\n" % \
                    (offset + int(function) - 1)

            if final:
                self.emit_stack_reorder(bindings, len(parameter))

            # apply takes number of parameter in rcx register
            self.text += "\tmov\trcx, %d\n" % (parameter_count)

            if final:
                self.compiler.extern.add("__apply.continue")
                self.text += "\tjmp\t__apply.continue\n"
            else:
                self.compiler.extern.add("__apply")
                self.text += "\tcall\t__apply\n"

                # remove local bindings
                if bindings > 0:
                    self.text += "\tadd\trsp, 8*%d\n" % (bindings)


        elif type(function) == LispList:
            self.emit_expression(function, offset=offset)

            if final:
                self.emit_stack_reorder(bindings, len(parameter))

            self.text += "\tmov\trcx, %d\n" % (parameter_count)

            if final:
                self.text += "\tjmp\t__apply.continue\n"
                self.compiler.extern.add("__apply.continue")
            else:
                self.text += "\tcall\t__apply\n"
                self.compiler.extern.add("__apply")
                # remove local bindings
                if bindings > 0:
                    self.text += "\tadd\trsp, 8*%d\n" % (bindings)

        elif type(function) == LispLambda:
            if function.argc is None:
                raise CompileError("%s: variadic lambda not allowed in local binding" % (function))
            if function.argc != parameter_count:
                raise CompileError("%s: expects %d parameter but got %d"
                        % (function, function_argc, parameter_count))

            self.emit_expression(function.body,
                                 bindings=bindings+len(parameter),
                                 final=final)

        elif type(function) == LispSym:
            function_label, function_argc = self.compiler.compile_symbol(function)
            if function_argc is not None and function_argc != parameter_count:
                raise CompileError("%s: expects %d parameter but got %d"
                        % (function, function_argc, parameter_count))

            if final:
                self.emit_stack_reorder(bindings, len(parameter))

            # if variadic, inform our function how many parameter it is receiving
            if function_argc is None:
                self.text += "\tmov\trcx, %d\n" % (parameter_count)

            if final:
                self.text += "\tjmp\t%s.continue\n" % (function_label)
            else:
                self.text += "\tcall\t%s\n" % (function_label)

                # remove local bindings
                if bindings > 0:
                    self.text += "\tadd\trsp, 8*%d\n" % (bindings)

        else:
            raise CompileError("%s: not executable" % (function))




    def emit_constant(self, expr, bindings=0,
                                  offset=0,
                                  final=False,
                                  save_rax_to_rbx=False,
                                  rax_zero=False):

        #print("[DEBUG] emit_constant: %s" % (expr))

        action = "jmp" if final else "call"
        sym = None

        if final and save_rax_to_rbx:
            raise CompileError("internal error - impossible combination of save_rax_to_rbx and final")


        if type(expr) == LispSym:
            sym = expr

            # hande special symbols
            if sym == "quote":
                if save_rax_to_rbx:
                    self.text += "\tmov\trbx, rax\n"

                self.text += "\tmov\tal, TYPE_QUOTE\n"
                self.text += "\tshl\trax, SHIFT_TYPE\n"

                self.emit_stack_reorder(bindings)
                if final:
                    self.text += "\tret\n"
                return

            # try to resolv symbol
            if sym not in self.compiler.env.symbols:
                raise CompileError("%s: undefined symbol" % (sym))
            expr = self.compiler.env.symbols[sym]


        if type(expr) == LispInt:
            self.emit_stack_reorder(bindings)
            if save_rax_to_rbx:
                self.text += "\tmov\trbx, rax\n"

            self.text += "\tmov\trax, %d\n" % (expr)
            self.text += "\t%s\t__mem_int\n" % (action)
            self.compiler.extern.add("__mem_int")


#        elif type(expr) == LispReal:
#            self.emit_stack_reorder(bindings)
#            if save_rax_to_rbx:
#                self.text += "\tpush\trax\n"
#            self.text += "\tmov\txmm0, %f\n" % (expr)
#            self.text += "\t%s\t__mem_real\n" % (action)
#            if save_rax_to_rbx:
#                self.text += "\tpop\trbx\n"

        elif type(expr) == LispRef:
            if save_rax_to_rbx:
                self.text += "\tmov\trbx, rax\n"

            self.text += "\tmov\trax, [rsp + 8*%d]\t; %s\n" % \
                    (offset + int(expr) - 1, expr)

            self.emit_stack_reorder(bindings)
            if final:
                self.text += "\tret\n"

        elif type(expr) == LispTrue:
            if save_rax_to_rbx:
                self.text += "\tmov\trbx, rax\n"

            self.text += "\tmov\tal, TYPE_TRUE\n"
            self.text += "\tshl\trax, SHIFT_TYPE\n"

            self.emit_stack_reorder(bindings)
            if final:
                self.text += "\tret\n"

        elif type(expr) == LispStr:
            label = self.compiler.get_string_label(expr)

            self.emit_stack_reorder(bindings)
            if save_rax_to_rbx:
                self.text += "\tpush\trax\n"

            self.text += "\tmov\trsi, %s\n" % (label)
            self.text += "\tmov\trbx, %d\n" % (len(expr))
            self.text += "\t%s\t__mem_string\n" % (action)
            self.compiler.extern.add("__mem_string")

            if save_rax_to_rbx:
                self.text += "\tpop\trbx\n"

        elif type(expr) == LispBuiltin or isinstance(expr, LispLambda):
            self.compiler.extern.add("__mem_lambda")
            function_label, function_argc = self.compiler.compile_expression(expr, sym)

            if save_rax_to_rbx:
                self.text += "\tpush\trax\n"

            self.text += "\tlea\trsi, [%s.continue]\n" % (function_label)
            if function_argc is None:
                self.text += "\tmov\trbx, LAMBDA_VARIADIC\n"
            elif function_argc == 0:
                self.text += "\txor\trbx, rbx\n"
            else:
                self.text += "\tmov\trbx, %d\n" % (function_argc)

            # are we dealing with a closure that actually captured something?
            if type(expr) == LispClosure and expr.capture_indices:
                # first create a lambda
                self.text += "\tcall\t__mem_lambda\n"

                # now let __mem_closure capture stack
                # please note, that we can not continue to __mem_closure,
                # because for that we must cleanup our stack... the exact thing
                # __mem_clousre is supposed to capture ;-)
                capture_label = self.compiler.get_capture_label(expr.capture_indices)
                self.text += "\tlea\trbx, [%s]\n" % (capture_label)
                self.text += "\tcall\t__mem_closure\n"
                self.compiler.extern.add("__mem_closure")

                # now we can clean up and go
                if save_rax_to_rbx:
                    self.text += "\tpop\trbx\n"
                self.emit_stack_reorder(bindings)
                if final:
                    self.text += "\tret\n"

            else:
                if final:
                    self.emit_stack_reorder(bindings)
                    self.text += "\tjmp\t__mem_lambda\n"
                else:
                    self.text += "\tcall\t__mem_lambda\n"
                    if save_rax_to_rbx:
                        self.text += "\tpop\trbx\n"
                    self.emit_stack_reorder(bindings)


        elif type(expr) == LispList:
            if len(expr) == 0:
                if save_rax_to_rbx:
                    self.text += "\tmov\trbx, rax\n"
                if not rax_zero:
                    self.text += "\txor\trax, rax\n"

                self.emit_stack_reorder(bindings)
                if final:
                    self.text += "\tret\n"

            else:
                self.compiler.extern.add("__cons")

                if save_rax_to_rbx:
                    self.text += "\tpush\trax\n"
                    offset += 1

                if not rax_zero:
                    self.text += "\txor\trax, rax\n"
                    rax_zero = True

                # we build our list in reverse with a series of __cons calls
                for item in reversed(expr[1:]):
                    self.emit_constant(item, offset=offset, save_rax_to_rbx=True, rax_zero=rax_zero)
                    self.text += "\tcall\t__cons\n"
                    rax_zero = False

                # now do our last cons
                self.emit_constant(expr[0], offset=offset, save_rax_to_rbx=True, rax_zero=rax_zero)
                if final:
                    self.emit_stack_reorder(bindings)
                    self.text += "\tjmp\t__cons\n"
                else:
                    self.text += "\tcall\t__cons\n"
                    # recover rbx from stack before removing all local bindings
                    if save_rax_to_rbx:
                        self.text += "\tpop\trbx\n"
                    self.emit_stack_reorder(bindings)

        else:
            raise CompileError("can't compile atom: %s" % (expr))
