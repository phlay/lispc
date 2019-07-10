#!/usr/bin/python3

import sys
import argparse

import environment
import compiler
from lisp import LispError


# parse arguments
#
parser = argparse.ArgumentParser(description="lisp x86_64")
parser.add_argument("files", metavar="file", nargs='*', help="lisp files to load")
parser.add_argument("-i", dest="interactive", help="interactive mode", action="store_true")
parser.add_argument("-s", dest="symbol", help="start symbol, default is main", default="main")
parser.add_argument("-c", dest="compile", help="compile", action="store_true")
parser.add_argument("-o", dest="output", help="compilation output file", default="a.out")
parser.add_argument("-a", dest="leave_asm", help="don't delete assembly file after compiling", action="store_true")
parser.add_argument("-p", dest="print", help="give assembly listing to stdout", action="store_true")

args = parser.parse_args()


# create an environment and load files into it
#
env = environment.Environment()

for fn in args.files:
    try:
        env.import_file(fn)

    except LispError as e:
        print('%s: Error: %s' % (fn, e))
        exit(1)
    except RecursionError:
        print('%s: Error: maximum recursion depth reached' % (fn))
        exit(1)
    except OSError as e:
        print("%s: can't open file: %s" % (fn, e.strerror))
        exit(1)



if args.compile or args.print:
    try:
        comp = compiler.Compiler(env, target=args.symbol)

        if args.print:
            sys.stdout.write(comp.get_assembly())
        else:
            comp.build(args.output, leave_asm=args.leave_asm)

    except LispError as e:
        print('Error: %s' % (e))
        exit(1)


elif args.interactive or len(args.files) == 0:
    for line in sys.stdin:
        try:
            line = line.strip()
            if not line:
                continue

            result = env.interpret_single_line(line)
            if result is not None:
                print("  = %s\n" % (result))

        except LispError as e:
            print('Error: %s\n' % (e))
        except RecursionError:
            print('Error: maximum recursion depth reached\n')

else:
    try:
        env.interpret_single_line('(%s)' % (args.symbol))

    except LispError as e:
        print('Error: %s' % (e))
        exit(1)
    except RecursionError:
        print('Error: maximum recursion depth reached')
        exit(1)
