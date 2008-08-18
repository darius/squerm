import glob

import initialscope
import interpret
import lispio
import processes
import scope
import syntax


def testme():
    for filename in glob.glob('eg/*.scm'):
        print '%s:' % filename
        runfile(filename)

def runfile(filename):
    run(open(filename).read())

def run(s):
    ev(tuple(lispio.read_iter(s)))

def ev(definitions):
    agenda = processes.Agenda()
    queue_scope = initialscope.make_universal_scope(agenda)
    scope = initialscope.make_os_scope(queue_scope, agenda)
    evaluate(agenda, definitions, scope)

def evaluate(agenda, definitions, scope):
#    print lispio.write(syntax.expand_toplevel(definitions))
    keeper = initialscope.ComplainingKeeper()
    expr = syntax.expand_toplevel(definitions)
    interpret.run(agenda, keeper, expr, scope)

if __name__ == '__main__':
    testme()
