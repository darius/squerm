from clutch import Clutch


# Environments

class EmptyScope:
    def get(self, var):
        raise 'Unbound variable', var

def OuterScope(frame):
    return _make_scope(dict(frame), EmptyScope())

def Scope(vars, vals, enclosing):
    return _make_scope(dict(zip(vars, vals)), enclosing)

def RecursiveScope(pairs, enclosing):
    frame = dict(pairs)
    scope = _make_scope(frame, enclosing)
    for var, value in pairs:
        frame[var] = value.make_closure(scope)
    return scope

def _make_scope(frame, enclosing):
    def to_get(var):
        return frame[var] if var in frame else enclosing.get(var)
    return Clutch(locals())
