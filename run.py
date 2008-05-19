import interpret
import lispio
import syntax


def runfile(name):
    run(open(name).read())

def run(s):
    ev(tuple(lispio.read_iter(s)))

def ev(definitions):
#    print lispio.write(syntax.expand_toplevel(definitions))
    return evaluate(definitions, interpret.universal_scope)

def evaluate(definitions, scope):
    interpret.running(syntax.expand_toplevel(definitions), scope)
