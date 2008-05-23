import os
import sys

from clutch     import Box, Clutch
import interpret
import lispio
from primitives import is_list, is_symbol, primitives_dict
from processes  import Primitive, RunningState, Process, ReceiverClass, \
                       Sender, SenderClass, sprout, StoppedState, WaitingState
from scope      import EmptyScope, OuterScope, RecursiveScope, Scope, ScopeClass
from symbols    import Symbol
import syntax


# Primitive procedures

def Apply():
    def to_call(args, k):
        fn, arglist = args
        return fn.call(arglist, k)
    def to___repr__():
        return '#<primitive apply>'
    return Clutch(locals())

def make_selector(method_name):
    if is_symbol(method_name):
        method_name = method_name.get_name()
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

def Choose():
    def to_call(args, k):
        (choices,) = args
        assert is_list(choices)
        for choice in choices:
            assert is_list(choice) and len(choice) == 2
            receiver, fn = choice
            assert isinstance(receiver, ReceiverClass)
        return WaitingState(choices, k)
    def to___repr__():
        return '#<primitive choose>'
    return Clutch(locals())

def Exit():
    def to_call(args, k):
        if len(args) == 0:
            return StoppedState()
        (plaint,) = args
        raise Exception(plaint)
    def to___repr__():
        return '#<primitive exit>'
    return Clutch(locals())

prims = dict((name, Primitive(fn)) for name, fn in primitives_dict.items())
prims.update({'apply':              Apply(),
              'make-selector':      Primitive(make_selector),
              'eval':               Eval(),
              'None':               None,
              'empty-environment':  EmptyScope(),
              'extend-environment': Primitive(extend_environment),
              'complaining-keeper': ComplainingKeeper(),
              'choose':             Choose(),
              'exit':               Exit(),
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
        assert opt_keeper is False or isinstance(opt_keeper, SenderClass)
        def SpawningState():
            def to_is_runnable(): return True
            def to_step():        return fn.call((), interpret.FinalK())
            def to_trace():       return '<spawning>'
            def to___repr__():    return '<spawning %r>' % fn
            return Clutch(locals())
        process = Process(opt_keeper, SpawningState())
        run_queue.enqueue(process)
        return process
    def sprout_fn():
        return sprout(run_queue.get_running_process(), run_queue)
    # TODO: add choice function
    return Scope(map(Symbol, ('spawn', 'sprout')),
                 map(Primitive, (spawn, sprout_fn)),
                 enclosing_scope)


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
