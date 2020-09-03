# SPDX-License-Identifier: Apache-2.0
# Copyright 2016 Eotvos Lorand University, Budapest, Hungary

import sys
import os
import pkgutil
import itertools

global filename
global filepath
global genfile
global outfile

filename = "?"
filepath = "?"
genfile = "?"
outfile = "?"

errors = []

warnings = []

def addError(where, msg):
    rootcwd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    import traceback
    sb  = traceback.extract_stack()
    res = list(itertools.dropwhile(lambda tb: tb[0] == 'src/compiler.py', sb))
    lineno = res[0][1]
    res = [(genfile, lineno, res[0][2], res[0][3])] + res[1:-1]

    try:
        with open(genfile) as f:
            lines = f.readlines()
            origlineno = int(lines[lineno+1].split(" ")[-1])

            with open(filepath) as f:
                origlines = f.readlines()
                res = [(filepath, origlineno, "...", origlines[origlineno].strip())] + res
    except:
        pass

    res = [(f".{path[len(rootcwd):]}" if path.startswith(rootcwd) else path, line, module, errmsg) for (path, line, module, errmsg) in res]

    global errors
    msg = "Error while {}: {}".format(where, msg)

    if pkgutil.find_loader('backtrace'):
        # uses the backtrace module to prettify output
        import backtrace
        btrace = backtrace._Hook(res, align=True)
        errors += [msg] + [f"    {msg}" for msg in btrace.generate_backtrace(backtrace.STYLES)]
    else:
        errors += [msg] + traceback.format_list(res)


def addWarning(where, msg):
    global warnings
    warnings += [f"WARNING: {msg} (While {where}).\n"]


def showErrors():
    global errors
    for e in errors:
        print(e, file=sys.stderr)


def showWarnings():
    global warnings
    for w in warnings:
        print(w, file=sys.stderr)


disable_hlir_messages = False


def build_hlir(hlir):
    """Builds the P4 internal representation, optionally disabling its output messages.
    Returns True if the compilation was successful."""
    if disable_hlir_messages:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    success = hlir.build()

    if disable_hlir_messages:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return success
