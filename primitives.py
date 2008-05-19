# Primitive procedures

def is_bool(x):    return isinstance(x, bool)
def is_symbol(x):  return isinstance(x, basestring)
def is_list(x):    return isinstance(x, tuple)
def is_pair(x):    return isinstance(x, tuple) and 0 < len(x)
def is_null(x):    return isinstance(x, tuple) and 0 == len(x)
def mklist(*args): return tuple(args)
def append(x, y):  return tuple(x) + y

def cons(x, y):
    assert is_list(y)
    return (x,) + y

def assoc(key, alist):
    assert is_list(alist)
    for pair in alist:
        assert is_list(pair)
	if pair[0] == key:
	    return pair
    return False

def member(key, ls):
    assert is_list(ls)
    for i, element in enumerate(ls):
	if key == element:
	    return ls[i:]
    return False

def car(x): return x[0]
def cdr(x): return x[1:]
def caar(x): return car(car(x))
def cadr(x): return car(cdr(x))
def cdar(x): return cdr(car(x))
def cddr(x): return cdr(cdr(x))
def caddr(x): return car(cdr(cdr(x)))
def cdddr(x): return cdr(cdr(cdr(x)))
def cadddr(x): return car(cdr(cdr(cdr(x))))

primitives_dict = {
    'pair?':   is_pair,
    'null?':   is_null,
    'symbol?': is_symbol,
    'list?':   is_list,
    'car':     car,
    'cdr':     cdr,
    'caar':    caar,
    'cadr':    cadr,
    'cdar':    cdar,
    'cddr':    cddr,
    'caddr':   caddr,
    'cadddr':  cadddr,
    'cons':    cons,
    'list':    mklist,
    'append':  append,
    'assoc':   assoc,
    'equal?':  lambda x, y: x == y,
    'not':     lambda arg: x is False,
    'member':  member,
}

def lmap(f, *xs): 
    return tuple(map(f, *xs))
