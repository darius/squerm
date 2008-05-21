import os
import sys

import interpret
import lispio
import processes
import scope
import syntax


def runfile(filename):
    run(open(filename).read())

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

def newline():
    sys.stdout.write('\n')

def make_os_scope(outer_scope):
    return scope.Scope(('write', 'newline', 'system'),
                       map(interpret.Primitive, (write, newline, os.system)),
                       outer_scope)
