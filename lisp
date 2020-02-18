#!/usr/bin/python3

import sys
import os
import argparse
import configparser

import environment
import compiler
from lisp import LispError


DEFAULT_CONFIG_PATH = "~/.lisp.ini"
DEFAULT_RUNTIME_PATH = "runtime"


# parse arguments
#
parser = argparse.ArgumentParser(description="lisp x86_64")
parser.add_argument("files", metavar="file", nargs='*',
                    help="lisp files to load")
parser.add_argument("-i", dest="interactive", action="store_true",
                    help="interactive mode")
parser.add_argument("-s", dest="symbol", default="main",
                    help="start symbol, default is main")
parser.add_argument("-c", dest="compile", action="store_true",
                    help="compile files to executable")
parser.add_argument("-o", dest="output", default="a.out",
                    help="compilation output file")
parser.add_argument("-a", dest="leave_asm", action="store_true",
                    help="don't delete assembly file after compiling")
parser.add_argument("-p", dest="print", action="store_true",
                    help="give assembly listing to stdout")

args = parser.parse_args()

# parse config file
#
conf = configparser.ConfigParser()
conf.read(os.path.expanduser(DEFAULT_CONFIG_PATH))


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
        comp = compiler.Compiler(env)
        comp.set_target_symbol(args.symbol)
        comp.set_leave_asm(args.leave_asm)
        comp.set_runtime(conf.get('compiler',
                                  'runtime',
                                  fallback=DEFAULT_RUNTIME_PATH))

        if args.print:
            sys.stdout.write(comp.get_assembly())
        else:
            comp.build(args.output)

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
    except KeyboardInterrupt:
        print()
        exit(1)
