import sys

import interpret
import lispio
import scope
import syntax


def runfile(name):
    run(open(name).read())

def run(s):
    ev(tuple(lispio.read_iter(s)))

def ev(definitions):
#    print lispio.write(syntax.expand_toplevel(definitions))
    return evaluate(definitions, os_scope)

def evaluate(definitions, scope):
    interpret.running(syntax.expand_toplevel(definitions), scope)


def write(x):
    sys.stdout.write(lispio.write(x))
    return True

def newline():
    sys.stdout.write('\n')
    return True

os_scope = scope.Scope(('write', 'newline'),
                       map(interpret.Primitive, (write, newline)),
                       interpret.universal_scope)
