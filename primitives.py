# Primitive procedures

def write(x):
    import sys
    import lispio
    sys.stdout.write(lispio.write(x))
    return 't'

def newline():
    import sys
    sys.stdout.write('\n')
    return 't'

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
    return 'nil'

def member(key, ls):
    assert is_list(ls)
    for i, element in enumerate(ls):
	if key == element:
	    return ls[i:]
    return 'nil'

def for_each(proc, ls):
    for element in ls:
	proc(element)

def predicate(f):
    return lambda x: make_flag(f(x))

def make_flag(x):
    return 't' if x else 'nil'

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
    'pair?':   predicate(is_pair),
    'null?':   predicate(is_null),
    'symbol?': predicate(is_symbol),
    'list?':   predicate(is_list),
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
    'equal?':  lambda x, y: make_flag(x == y),
    'not':     lambda arg: make_flag(x == 'nil'),
    'member':  member,
    'write':   write,           # XXX move capabilities out of
    'newline': newline,         #  the top-level environment
}

def lmap(f, *xs): 
    return tuple(map(f, *xs))
