from clutch     import Box, Clutch
from primitives import *
from processes  import RunningState, Process, StoppedState
from scope      import RecursiveScope, Scope


# Processes

def run(agenda, opt_keeper, expr, scope):
    agenda.enqueue(Process(opt_keeper, StartingEvalState(expr, scope)))
    agenda.run()

def StartingEvalState(expr, scope):
    def to_is_runnable(): return True
    def to_step():        return expr.eval(scope, FinalK())
    def to_trace():       return '<starting>'
    def to___repr__():    return '<starting %r>' % expr
    return Clutch(locals())


# Continuations

class Cont(Clutch):
    def __str__(self):
        return '\n'.join(reversed(self.get_backtrace()))
    def __repr__(self):
        return '|'.join(self.get_backtrace())
    def get_backtrace(self):
        return [k.show_frame() for k in ancestry(self)]
        
def ancestry(k):
    while True:
        yield k
        k = k.get_parent()
        if k is None:
            break

def FinalK():
    def to_step(value):
        return StoppedState()
    def to_show_frame():
        return '<stop>'
    def to_get_parent():
        return None
    return Cont(locals())


# The interpreter proper

def BeginExpr(expr1, expr2):
    def to_eval(scope, k):
        return expr1.eval(scope, IgnoreK(expr2, scope, k))
    def to___repr__():
        return '(begin %r %r)' % (expr1, expr2)
    return Clutch(locals())

def IgnoreK(expr, scope, k):
    def to_step(value):
        return expr.eval(scope, k)
    def to_show_frame():
        return '(begin <#> %r)' % expr
    def to_get_parent():
        return k
    return Cont(locals())

def CallExpr(rator, rands):
    def to_eval(scope, k):
        return rator.eval(scope, EvRandsK(rands, scope, k, rator))
    def to___repr__():
        return '(%r%s)' % (rator, ''.join(' %r' % rand for rand in rands))
    return Clutch(locals())

def EvRandsK(rands, scope, k, rator):
    def to_step(fn):
        if is_null(rands):
            return fn.call((), k)
        return rands[0].eval(scope,
                             EvMoreRandsK(fn, (), rands[1:], scope, k,
                                          rator, rands[:1]))
    def to_show_frame():
        return '(<%r>%s)' % (rator, ''.join(' %r' % rand for rand in rands))
    def to_get_parent():
        return k
    return Cont(locals())

def EvMoreRandsK(fn, args, rands, scope, k, rator, prev_rands):
    def to_step(arg):
        new_args = args + (arg,)
        if is_null(rands):
            return fn.call(new_args, k)
        return rands[0].eval(scope,
                             EvMoreRandsK(fn, new_args, rands[1:], scope, k,
                                          rator, prev_rands + rands[:1]))
    def to_show_frame():
        prev = '%r%s' % (rator, 
                         ''.join(' %r' % rand for rand in prev_rands))
        return '(<%s>%s)' % (prev,
                             ''.join(' %r' % rand for rand in rands))
    def to_get_parent():
        return k
    return Cont(locals())

def ConstantExpr(value):
    def to_eval(scope, k):
        return RunningState(value, k)
    def to___repr__():
        return "'" + repr(value)
    return Clutch(locals())

def LetrecprocExpr(pairs, body):
    for var, proc in pairs:
        assert isinstance(proc, LambdaExprClass), \
            'Bad syntax in locals: %r' % pairs
    def to_eval(scope, k):
        return body.eval(RecursiveScope(pairs, scope), k)
    def to___str__():
        return to___repr__()
    def to___repr__():
        return '(local (%s) %r)' % (' '.join(('(define %s %r)' 
                                              % (var, proc))
                                             for var, proc in pairs),
                                    body)
    return Clutch(locals())

def IfExpr(test_expr, then_expr, else_expr):
    def to_eval(scope, k):
        return test_expr.eval(scope, TestK(then_expr, else_expr, scope, k))
    def to___repr__():
        return '(if %r %r %r)' % (test_expr, then_expr, else_expr)
    return Clutch(locals())

def TestK(then_expr, else_expr, scope, k):
    def to_step(value):
        return (else_expr if value is False else then_expr).eval(scope, k)
    def to_show_frame():
        return '(if <#> %r %r)' % (then_expr, else_expr)
    def to_get_parent():
        return k
    return Cont(locals())
    
def LambdaExpr(variables, expr):
    def to_eval(scope, k):
        return RunningState(Procedure(scope, variables, expr), k)
    def to___repr__():
        return '(lambda (%s) %r)' % (' '.join(map(repr, variables)),
                                     expr)
    def to_make_closure(scope):
        return Procedure(scope, variables, expr)
    return LambdaExprClass(locals())

class LambdaExprClass(Clutch): pass

def Procedure(scope, variables, expr):
    def to_call(args, k):
        assert len(variables) == len(args), \
            "Arguments %r don't match parameters %r" % (args, variables)
        return expr.eval(Scope(variables, args, scope), k)
    def to___repr__():
        return '#<procedure>'
    return Clutch(locals())

def VarRefExpr(variable):
    def to_eval(scope, k):
        return RunningState(scope.get(variable), k)
    def to___repr__():
        return repr(variable)
    return Clutch(locals())
