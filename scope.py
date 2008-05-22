from clutch import Clutch


# Environments

class ScopeClass(Clutch):
    def __repr__(self):
        return '#<environment>'

def EmptyScope():
    def to_get(var):
         # XXX what type of exception should this be?
        raise Exception('Unbound variable', var)
    return ScopeClass(locals())

def OuterScope(frame):
    return _make_scope(dict(frame), EmptyScope())

def Scope(vars, vals, enclosing):
    return _make_scope(dict(zip(vars, vals)), enclosing)

def RecursiveScope(pairs, enclosing):
    frame = dict(pairs)
    scope = _make_scope(frame, enclosing)
    for var, expr in pairs:
        frame[var] = expr.make_closure(scope)
    return scope

def _make_scope(frame, enclosing):
    assert isinstance(enclosing, ScopeClass)
    def to_get(var):
        return frame[var] if var in frame else enclosing.get(var)
    return ScopeClass(locals())
