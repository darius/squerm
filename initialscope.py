import os
import sys

from clutch import Box, Clutch
import interpret
import lispio
from primitives import is_list, is_symbol, primitives_dict
from processes import RunningState, Process
from scope import EmptyScope, OuterScope, RecursiveScope, Scope, ScopeClass
import syntax


# Primitive procedures

def Primitive(fn):
    def to_call(args, k):
        try:
            result = fn(*args)
        except Exception, e:
            print k
            raise
        return RunningState(result, k)
    def to___repr__():
        return '#<primitive %s>' % fn.__name__
    return Clutch(locals())

def Apply():
    def to_call(args, k):
        fn, arglist = args
        return fn.call(arglist, k)
    def to___repr__():
        return '#<primitive apply>'
    return Clutch(locals())

def Eval():
    def to_call(args, k):
        sexpr, scope = args
        assert isinstance(scope, ScopeClass)
        return syntax.expand_exp(sexpr).eval(scope, k)
    def to___repr__():
        return '#<primitive eval>'
    return Clutch(locals())

def extend_environment(vars, vals, scope):
    assert is_list(vars)
    for var in vars:
        assert is_symbol(var)
    assert is_list(vals)
    assert len(vars) == len(vals)
    return Scope(vars, vals, scope)

prims = dict((name, Primitive(fn)) for name, fn in primitives_dict.items())
prims.update({'apply': Apply(),
              'eval':  Eval(),
              'None':  None,
              'empty-environment': EmptyScope(),
              'extend-environment': Primitive(extend_environment)})

def RecursiveScopeExpr():
    def to_make_closure(scope): return scope
    def to___repr__():          return '<recursive-scope-expr>'
    return Clutch(locals())

safe_scope = RecursiveScope(zip(('safe-environment',),
                                (RecursiveScopeExpr(),)),
                            OuterScope(prims))

def make_universal_scope(run_queue):
    return add_process_functions(safe_scope, run_queue)

def add_process_functions(enclosing_scope, run_queue):
    def spawn(opt_keeper, fn):
        # TODO: check that opt_keeper is a sender or #f
        def SpawningState():
            def to_is_runnable(): return True
            def to_step():        return fn.call((Receive(), send_fn),
                                                 interpret.FinalK())
            def to_trace():       return '<spawning>'
            return Clutch(locals())
        def send(message):
            process.accept(message, run_queue)
        send_fn = Primitive(send)
        def Receive():
            def to_call(args, k):
                assert () == args
                assert process == run_queue.get_running_process()
                return process.receive(k)
            def to___repr__():
                return '#<?>'
            return Clutch(locals())
        process = Process(opt_keeper, SpawningState())
        run_queue.enqueue(process)
        return send_fn
    return Scope(('spawn',), (Primitive(spawn),), enclosing_scope)


def write(x):
    sys.stdout.write(lispio.write(x))

def newline():
    sys.stdout.write('\n')

def make_os_scope(outer_scope):
    return Scope(('write', 'newline', 'system'),
                 map(Primitive, (write, newline, os.system)),
                 outer_scope)
