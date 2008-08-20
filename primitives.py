import operator

from symbols import Symbol, SymbolClass


# Primitive procedures

def is_bool(x):    return isinstance(x, bool)
def is_number(x):  return isinstance(x, (int, long, float))
def is_string(x):  return isinstance(x, basestring)
def is_symbol(x):  return isinstance(x, SymbolClass)
def is_list(x):    return isinstance(x, tuple)
def is_pair(x):    return isinstance(x, tuple) and 0 < len(x)
def is_null(x):    return x == ()
def mklist(*args): return tuple(args)

def cons(x, y):
    assert is_list(y), 'Second argument to cons must be a list: %r' % y
    return (x,) + y

def car(x):
    assert is_list(x) and 1 <= len(x), \
        'Argument to car must be a nonnull list: %r' % x
    return x[0]
def cdr(x):
    assert is_list(x) and 1 <= len(x), \
        'Argument to cdr must be a nonnull list: %r' % x
    return x[1:]

def sub(*args):
    if 1 == len(args):
        return -args[0]
    if 2 == len(args):
        return args[0] - args[1]
    raise TypeError('- expected 1 or 2 arguments')

def append(x, y):  return tuple(x) + y

def assoc(key, alist):
    assert is_list(alist), \
        'Second argument to assoc must be an a-list: %r' % alist
    for pair in alist:
        assert is_list(pair), \
            'Second argument to assoc must be an a-list: %r' % alist
        if pair[0] == key:
            return pair
    return False

def member(key, ls):
    assert is_list(ls), 'Second argument to member must be a list: %r' % ls
    for i, element in enumerate(ls):
        if key == element:
            return ls[i:]
    return False

def caar(x): return car(car(x))
def cadr(x): return car(cdr(x))
def cdar(x): return cdr(car(x))
def cddr(x): return cdr(cdr(x))
def caaar(x): return car(car(car(x)))
def caadr(x): return car(car(cdr(x)))
def cadar(x): return car(cdr(car(x)))
def caddr(x): return car(cdr(cdr(x)))
def cdaar(x): return cdr(car(car(x)))
def cdadr(x): return cdr(car(cdr(x)))
def cddar(x): return cdr(cdr(car(x)))
def cdddr(x): return cdr(cdr(cdr(x)))
def cadddr(x): return car(cdr(cdr(cdr(x))))

def head(x, n): return x[:n]
def tail(x, n): return x[n:]

def string_from_number(n):
    assert isinstance(n, (int, float))
    return '%s' % n

primitives_dict = {
    'boolean?': is_bool,
    'number?': is_number,
    'string?': is_string,
    'symbol?': is_symbol,
    'list?':   is_list,
    'pair?':   is_pair,
    'null?':   is_null,
    'list':    mklist,
    'cons':    cons,
    'car':     car,
    'cdr':     cdr,
    '+':       operator.add,
    '-':       sub,
    '*':       operator.mul,
    '/':       operator.truediv,
    'quotient':  operator.div,
    'remainder': operator.mod,
#    'modulo': operator.,
    'abs':     operator.abs,
    '<':       operator.lt,     # XXX do we want Python's behavior?
    '<=':      operator.le,
    '=':       operator.eq,
    '>':       operator.gt,
    '>=':      operator.ge,
    'expt':    operator.pow,
    'equal?':  lambda x, y: x == y,

    'append':  append,
    'assoc':   assoc,
    'member':  member,
    'caar':    caar,
    'cadr':    cadr,
    'cdar':    cdar,
    'cddr':    cddr,
    'caaar':   caaar,
    'caadr':   caadr,
    'cadar':   cadar,
    'caddr':   caddr,
    'cdaar':   cdaar,
    'cdadr':   cdadr,
    'cddar':   cddar,
    'cdddr':   cdddr,
    'cadddr':  cadddr,
    'not':     lambda x: x is False,
    'head':    head,
    'tail':    tail,

    'chr':     chr,
    'ord':     ord,
    'string<-number': string_from_number,
    'length':  len,
    'get':     lambda x, key: x[key],
    'slice':   lambda x, lo, hi=None: x[lo:hi],
    'max':     max,
    'min':     min,
}
