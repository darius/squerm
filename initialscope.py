import os
import sys

from clutch import Box, Clutch
import interpret
import lispio
from primitives import is_list, is_symbol, primitives_dict
from processes import RunningState, Process, Sender, SenderClass
from scope import EmptyScope, OuterScope, RecursiveScope, Scope, ScopeClass
from symbols import Symbol
import syntax


# Primitive procedures

def Primitive(fn):
    def to_call(args, k):
        return RunningState(fn(*args), k)
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

def make_selector(method_name):
    assert isinstance(method_name, basestring)
    assert not method_name.startswith('_')
    return Selector(method_name)

# Whitelist of types whose methods preserve capability discipline.
invocable_types = (basestring, frozenset)

def Selector(method_name):
    def to_call(args, k):
        object = args[0]
        assert isinstance(object, invocable_types)
        arguments = args[1:]
        return RunningState(getattr(object, method_name)(*arguments),
                            k)
    def to___repr__():
        return '#<selector %s>' % method_name
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

def ComplainingKeeper():
    def to_send(message):
        print message
    def to_call(args, k):
        (message,) = args
        to_send(message)
        return RunningState(None, k)        
    def to___repr__():
        return '#<! complaining-keeper>'
    return SenderClass(locals())

prims = dict((name, Primitive(fn)) for name, fn in primitives_dict.items())
prims.update({'apply':              Apply(),
              'make-selector':      Primitive(make_selector),
              'eval':               Eval(),
              'None':               None,
              'empty-environment':  EmptyScope(),
              'extend-environment': Primitive(extend_environment),
              'complaining-keeper': ComplainingKeeper(),
              })
prims = dict((Symbol(name), value) for name, value in prims.items())

def RecursiveScopeExpr():
    def to_make_closure(scope): return scope
    def to___repr__():          return '<recursive-scope-expr>'
    return Clutch(locals())

safe_scope = RecursiveScope(zip((Symbol('safe-environment'),),
                                (RecursiveScopeExpr(),)),
                            OuterScope(prims))

def make_universal_scope(run_queue):
    return add_process_functions(safe_scope, run_queue)

def add_process_functions(enclosing_scope, run_queue):
    def spawn(opt_keeper, fn):
        if opt_keeper is not False:
            assert isinstance(opt_keeper, SenderClass)
        def SpawningState():
            def to_is_runnable(): return True
            def to_step():        return fn.call((Receive(), sender),
                                                 interpret.FinalK())
            def to_trace():       return '<spawning>'
            def to___repr__():    return '<spawning %r>' % fn
            return Clutch(locals())
        def Receive():
            def to_call(args, k):
                assert () == args
                assert process == run_queue.get_running_process()
                return process.receive(k)
            def to___repr__():
                return '#<? %r>' % process
            return Clutch(locals())
        process = Process(opt_keeper, SpawningState())
        run_queue.enqueue(process)
        sender = Sender(process, run_queue)
        return sender
    return Scope((Symbol('spawn'),), (Primitive(spawn),), enclosing_scope)


def write(x):
    sys.stdout.write(lispio.write(x))

def newline():
    sys.stdout.write('\n')

def print_(x):
    write(x)
    newline()

def make_os_scope(outer_scope):
    return Scope(map(Symbol, ('write', 'newline', 'print', 'system')),
                 map(Primitive, (write, newline, print_, os.system)),
                 outer_scope)
