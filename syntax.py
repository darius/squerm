from clutch import Clutch, Box
from interpret import *
from primitives import *


# Concrete syntax

def expand_toplevel(definitions):

    def expand(exp):
	if is_symbol(exp):
	    return VarRefExpr(exp)
	if is_null(exp) or is_bool(exp):
	    return ConstantExpr(exp)
        assert is_pair(exp)
	rator = car(exp)
	if is_symbol(rator) and rator in expanders:
	    return expanders[rator](exp)
	if is_symbol(rator) and rator in macros:
	    return expand(macros[rator](exp))
	fn = expand(rator)
	arguments = tuple(expand(e) for e in cdr(exp))
	return CallExpr(fn, arguments)

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
	else_expr = (False if len(exp) == 3 else exp[3])
	return IfExpr(expand(cadr(exp)),
		      expand(caddr(exp)),
		      expand(else_expr))

    def expand_lambda(exp):
	return LambdaExpr(cadr(exp), expand(make_begin(cddr(exp))))

    def expand_local(exp):
        definitions = exp[1]
        body = ('begin',) + exp[2:]
        return LetrecprocExpr(map(expand_define, definitions),
                              expand(body))

    def expand_define(exp):
        # N.B. not an expression type
	if is_symbol(cadr(exp)):
	    variable = cadr(exp)
	    value_expr = caddr(exp)
	elif is_pair(cadr(exp)):
	    variable = car(cadr(exp))
	    value_expr = cons('lambda', cons(cdr(cadr(exp)), cddr(exp)))
	else:
	    raise 'Bad syntax', exp
	return (variable, expand(value_expr))

    def expand_quote(exp):
	return ConstantExpr(cadr(exp))

    expanders = {
	'begin':      expand_begin,
	'if':         expand_if,
	'lambda':     expand_lambda,
	'local':      expand_local,
	'quote':      expand_quote,
	}

    return expand_local(mklist('local', definitions, ('main',)))


# Macros

def macroexpand_1(exp):
    if not is_pair(exp):
	return exp
    rator = car(exp)
    if is_symbol(rator) and rator in macros:
	return macros[rator](exp)
    else:
        return exp

gensym_counter = 0

def gensym():
    global gensym_counter
    gensym_counter += 1
    return '#G%s' % gensym_counter

def make_begin(exps):
    if len(exps) == 1:
	return car(exps)
    else:
	return cons('begin', exps)


def macro_and(exp):
    if len(exp) == 1:
	return True
    elif len(exp) == 2:
	return cadr(exp)
    else:
	return mklist('if', cadr(exp), 
		      cons('and', cddr(exp)),
                      False)

def macro_case(exp):
    subject = cadr(exp)
    clauses = cddr(exp)
    defaults = (clauses[-1][0] == 'else')
    if defaults:
	default_exps = cdr(clauses[-1])
	clauses = clauses[:-1]
    # (case subject ((x y) exp) ... (else default)) ==>
    # (let ((var subject)) (cond ((member var '(x y)) exp) ... (else default)))
    var = gensym()
    branches = [translate_case_clause(var, car(clause), cdr(clause))
		for clause in clauses]
    if defaults:
	branches.append(cons('else', default_exps))
    return mklist(mklist('lambda', mklist(var), 
			 cons('cond', tuple(branches))),
		  subject)

def translate_case_clause(var, constants, exps):
    if len(constants) == 1:
	test = mklist('equal?', var, mklist('quote', car(constants)))
    else:
	test = mklist('member', var, mklist('quote', constants))
    return cons(test, exps)

def macro_cond(exp):
    if len(exp) == 1:
	# (cond) ==> #f
	r = False
    elif len(exp) == 2 and car(cadr(exp)) == 'else':
	# (cond (else x...)) ==> (begin x...)
	r = make_begin(cdr(cadr(exp)))
    elif len(cadr(exp)) == 1:
	# (cond (x) y...) ==> (or x (cond y...))
	r = mklist('or', car(cadr(exp)), cons('cond', cddr(exp)))
    elif len(cadr(exp)) == 3 and cadr(cadr(exp)) == '=>':
	# (cond (x => y) z...) ==> 
	# (let ((t x))
	#   (if t (y t) (cond z...)))
	t = gensym()
	r = mklist('let',
		   mklist(mklist(t, car(cadr(exp)))),
		   mklist('if', t, mklist(caddr(cadr(exp)), t),
			  cons('cond', cddr(exp))))
    else:
	# (cond (x y...) z...) ==> (if x (begin y...) (cond z...))
	r = mklist('if', car(cadr(exp)), make_begin(cdr(cadr(exp))),
		   cons('cond', cddr(exp)))
    return r

def macro_let(exp):
    if is_symbol(cadr(exp)):
	return macro_named_let(exp)
    # (let ((v e) ...) body...) ==>
    # ((lambda (v...) body...) e...)
    vars = lmap(car, cadr(exp))
    exps = lmap(cadr, cadr(exp))
    body = cddr(exp)
    return cons(cons('lambda', cons(vars, body)),
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
    return cons(mklist('local',
		       mklist(cons('define', cons(cons(proc, vars), body))),
		       proc),
		exps)

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
	return mklist(mklist('lambda', mklist('p', 'fail'),
			     mklist('if', 'p', 'p', mklist('fail'))),
		      cadr(exp),
		      mklist('lambda', (), cons('or', cddr(exp))))

macros = {
    'and':        macro_and,
    'case':       macro_case,
    'cond':       macro_cond,
    'let':        macro_let,
    'or':         macro_or,
    }
