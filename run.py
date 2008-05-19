import sys

import interpret
import lispio
import processes
import scope
import syntax


def runfile(name):
    run(open(name).read())

def run(s):
    ev(tuple(lispio.read_iter(s)))

def ev(definitions):
    run_queue = processes.RunQueue()
    queue_scope = interpret.make_universal_scope(run_queue)
    evaluate(run_queue, definitions, make_os_scope(queue_scope))

def evaluate(run_queue, definitions, scope):
#    print lispio.write(syntax.expand_toplevel(definitions))
    interpret.run(run_queue, syntax.expand_toplevel(definitions), scope)


def write(x):
    sys.stdout.write(lispio.write(x))
    return True

def newline():
    sys.stdout.write('\n')
    return True

def make_os_scope(outer_scope):
    return scope.Scope(('write', 'newline'),
                       map(interpret.Primitive, (write, newline)),
                       outer_scope)
