import itertools

from clutch import Clutch, Box
from interpret import *
from primitives import *


def _make_symbols(string):
    return map(Symbol, string.split())

_and, _begin, _cond, _case, _define, _else, _equalP, _exit = \
    _make_symbols('and begin cond case define else equal? exit')
_fail, _if, _lambda, _let, _local, _main, _make_selector, _member, _or = \
    _make_symbols('fail if lambda let local main make-selector member or')
_p, _quote, _selector = \
    _make_symbols('p quote selector')
_arrow = Symbol('=>')
_append, _cons, _quasiquote, _unquote, _unquote_splicing = \
    _make_symbols('append cons quasiquote unquote unquote-splicing')
_car, _cdr, _match_error, _mcase, _mlambda, _mlet, _not, _pairP = \
    _make_symbols('car cdr match-error mcase mlambda mlet not pair?')


# Concrete syntax

def expand_toplevel(definitions):
    return expand_exp(mklist(_local, definitions, (_main,)))

def expand_exp(the_exp):

    def expand(exp):
        if is_symbol(exp):
            return VarRefExpr(exp)
        if is_null(exp) or is_bool(exp) or is_string(exp) or is_number(exp):
            return ConstantExpr(exp)
        assert is_pair(exp), 'Non-self-evaluating literal: %r' % exp
        rator = car(exp)
        if is_symbol(rator) and rator in expanders:
            return expanders[rator](exp)
        if is_symbol(rator) and rator in macros:
            return expand(macros[rator](exp))
        return CallExpr(expand(rator), lmap(expand, cdr(exp)))

    # XXX check syntax

    def expand_begin(exp):
        exps = cdr(exp)
        if len(exps) == 0:
            return False
        elif len(exps) == 1:
            return expand(car(exps))
        else:
            return BeginExpr(expand(car(exps)),
                             expand(make_begin(cdr(exps))))

    def expand_if(exp):
        else_exp = (False if len(exp) == 3 else exp[3])
        return IfExpr(expand(cadr(exp)),
                      expand(caddr(exp)),
                      expand(else_exp))

    def expand_lambda(exp):
        return LambdaExpr(cadr(exp), expand(make_begin(cddr(exp))))

    def expand_local(exp):
        definitions = exp[1]
        body = (_begin,) + exp[2:]
        return LetrecprocExpr(map(expand_define, definitions),
                              expand(body))

    def expand_define(exp):
        # N.B. not an expression type
        if is_symbol(cadr(exp)):
            variable = cadr(exp)
            value_exp = caddr(exp)
        elif is_pair(cadr(exp)):
            variable = car(cadr(exp))
            value_exp = cons(_lambda, cons(cdr(cadr(exp)), cddr(exp)))
        else:
            raise Exception('Bad syntax', exp)
        return (variable, expand(value_exp))

    def expand_quote(exp):
        return ConstantExpr(cadr(exp))

    expanders = {
        _begin:  expand_begin,
        _if:     expand_if,
        _lambda: expand_lambda,
        _local:  expand_local,
        _quote:  expand_quote,
        }

    return expand(the_exp)


# Macros

def macroexpand_1(exp):
    if not is_pair(exp):
        return exp
    rator = car(exp)
    if is_symbol(rator) and rator in macros:
        return macros[rator](exp)
    else:
        return exp

gensym_counter = itertools.count(1)

def gensym():
    return Symbol('#G%s' % gensym_counter.next())

def make_begin(exps):
    if len(exps) == 1:
        return car(exps)
    else:
        return cons(_begin, exps)


def macro_and(exp):
    if len(exp) == 1:
        return True
    elif len(exp) == 2:
        return cadr(exp)
    else:
        return mklist(_if, cadr(exp), 
                      cons(_and, cddr(exp)),
                      False)

def macro_case(exp):
    subject = cadr(exp)
    clauses = cddr(exp)
    if clauses and clauses[-1][0] == _else:
        default_exps = cdr(clauses[-1])
        clauses = clauses[:-1]
    else:
        default_exps = mklist(mklist(_exit, "case match failed"))
    # (case subject ((x y) exp) ... (else default)) ==>
    # (let ((var subject)) (cond ((member var '(x y)) exp) ... (else default)))
    var = gensym()
    branches = [translate_case_clause(var, car(clause), cdr(clause))
                for clause in clauses]
    branches.append(cons(_else, default_exps))
    return mklist(mklist(_lambda, mklist(var), 
                         cons(_cond, tuple(branches))),
                  subject)

def translate_case_clause(var, constants, exps):
    if len(constants) == 1:
        test = mklist(_equalP, var, mklist(_quote, car(constants)))
    else:
        test = mklist(_member, var, mklist(_quote, constants))
    return cons(test, exps)

def macro_cond(exp):
    if len(exp) == 1:
        # (cond) ==> #f
        r = mklist(mklist(_exit, "no cond clause taken"))
    elif len(exp) == 2 and car(cadr(exp)) == _else:
        # (cond (else x...)) ==> (begin x...)
        r = make_begin(cdr(cadr(exp)))
    elif len(cadr(exp)) == 1:
        # (cond (x) y...) ==> (or x (cond y...))
        r = mklist(_or, car(cadr(exp)), cons(_cond, cddr(exp)))
    elif len(cadr(exp)) == 3 and cadr(cadr(exp)) == _arrow:
        # (cond (x => y) z...) ==> 
        # (let ((t x))
        #   (if t (y t) (cond z...)))
        t = gensym()
        r = mklist(_let,
                   mklist(mklist(t, car(cadr(exp)))),
                   mklist(_if, t, mklist(caddr(cadr(exp)), t),
                          cons(_cond, cddr(exp))))
    else:
        # (cond (x y...) z...) ==> (if x (begin y...) (cond z...))
        r = mklist(_if, car(cadr(exp)), make_begin(cdr(cadr(exp))),
                   cons(_cond, cddr(exp)))
    return r

def macro_let(exp):
    if is_symbol(cadr(exp)):
        return macro_named_let(exp)
    # (let ((v e) ...) body...) ==>
    # ((lambda (v...) body...) e...)
    vars = lmap(car, cadr(exp))
    exps = lmap(cadr, cadr(exp))
    body = cddr(exp)
    return cons(cons(_lambda, cons(vars, body)),
                exps)

def macro_named_let(exp):
    proc = cadr(exp)
    vars = lmap(car, caddr(exp))
    exps = lmap(cadr, caddr(exp))
    body = cdddr(exp)
    # (let proc ((var exp)...) body) ==>
    # ((local ((define (proc var...) body))
    #    proc)
    #  exp...)
    return cons(mklist(_local,
                       mklist(cons(_define, cons(cons(proc, vars), body))),
                       proc),
                exps)

def macro_mcase(exp):
    subject = cadr(exp)
    clauses = cddr(exp)
    # (mcase subject (pattern action) ...) ==>
    # ((mlambda (pattern action) ...) subject)
    return mklist(cons(_mlambda, clauses),
                  subject)

def macro_mlet(exp):
    # (mlet (pattern subject) body ...) ==>
    # ((mlambda (pattern body ...)) subject)
    binding = cadr(exp)
    body = cddr(exp)
    pattern = car(binding)
    subject = cadr(binding)
    return mklist(mklist(_mlambda, cons(pattern, body)), subject)

def macro_mlambda(exp):
    clauses = cdr(exp)
    if is_null(clauses):
        return _match_error
    subject, fail = gensym(), gensym()
    return mklist(_lambda, mklist(subject),
                  mklist(_let, mklist(mklist(fail,
                                             mklist(_lambda, (),
                                                    cons(_mcase,
                                                         cons(subject,
                                                              cdr(clauses)))))),
                         expand_pattern(subject, caar(clauses),
                                        mklist(fail), cons(_begin, cdar(clauses)))))

def expand_pattern(subject, pat, fail, succeed):
    def test(literal):
        return mklist(_if, mklist(_not, mklist(_equalP, subject, literal)),
                      fail,
                      succeed)
    if is_symbol(pat):
        return mklist(_let, mklist(mklist(pat, subject)), succeed)
    elif not is_pair(pat):
        return test(mklist(_quote, pat))
    elif car(pat) == _quote:
        return test(pat)
    else:
        return mklist(_if, mklist(_not, mklist(_pairP, subject)),
                      fail,
                      expand_pattern(mklist(_car, subject),
                                     car(pat),
                                     fail,
                                     expand_pattern(mklist(_cdr, subject),
                                                    cdr(pat),
                                                    fail,
                                                    succeed)))

def macro_or(exp):
    if len(exp) == 1:
        return False
    elif len(exp) == 2:
        return cadr(exp)
    else:
        # (or x y...) ==>
        # ((lambda (p fail) (if p p (fail)))
        #  x
        #  (lambda () (or y ...)))
        return mklist(mklist(_lambda, mklist(_p, _fail),
                             mklist(_if, _p, _p, mklist(_fail))),
                      cadr(exp),
                      mklist(_lambda, (), cons(_or, cddr(exp))))

def macro_selector(exp):
    return mklist(_make_selector, mklist(_quote, cadr(exp)))

def macro_quasiquote(exp):
    # XXX doesn't do nesting
    return qquote(cadr(exp))

def qquote(exp):
    if not is_pair(exp):
        if is_constant(exp): return exp
        return mklist(_quote, exp)
    if car(exp) == _unquote:
        return cadr(exp)
    if is_pair(car(exp)) and caar(exp) == _unquote_splicing:
        if is_null(cdr(exp)):
            return cadar(exp)
        return mklist(_append, cadar(exp), qquote(cdr(exp)))
    return combine_skeletons(qquote(car(exp)), qquote(cdr(exp)), exp)

def combine_skeletons(left, right, exp):
    if is_constant(left) and is_constant(right):
        L, R = qquote_eval(left), qquote_eval(right)
        if car(exp) == L and cdr(exp) == R:
            return mklist(_quote, exp)
        return mklist(_quote, cons(L, R))
    return mklist(_cons, left, right)

def qquote_eval(constant):
    if is_pair(constant):       # Is this a (quote foo) form?
        return cadr(constant)
    return constant

def is_constant(exp):
    if is_pair(exp):
        return car(exp) == _quote
    return is_number(exp)       # XXX more cases

macros = {
    _and:        macro_and,
    _case:       macro_case,
    _cond:       macro_cond,
    _let:        macro_let,
    _mcase:      macro_mcase,
    _mlambda:    macro_mlambda,
    _mlet:       macro_mlet,
    _or:         macro_or,
    _selector:   macro_selector,
    _quasiquote: macro_quasiquote,
    }

def lmap(f, *xs): 
    return tuple(map(f, *xs))
