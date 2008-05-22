import initialscope
import interpret
import lispio
import processes
import scope
import syntax


def testme():
    for p in range(6):
        print '%d:' % p
        runfile('eg/%d.scm' % p)

def runfile(filename):
    run(open(filename).read())

def run(s):
    ev(tuple(lispio.read_iter(s)))

def ev(definitions):
    run_queue = processes.RunQueue()
    queue_scope = initialscope.make_universal_scope(run_queue)
    evaluate(run_queue, definitions, initialscope.make_os_scope(queue_scope))

def evaluate(run_queue, definitions, scope):
#    print lispio.write(syntax.expand_toplevel(definitions))
    keeper = initialscope.ComplainingKeeper()
    expr = syntax.expand_toplevel(definitions)
    interpret.run(run_queue, keeper, expr, scope)
