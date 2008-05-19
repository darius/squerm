import clutch


# Reading s-expressions

class EOF:
    def isspace(self):
	return False
eof = EOF()

def read_iter(input):

    i = clutch.Box(0)

    def token():
	result = input[i._ : i._+1]
	if result == '':
	    result = eof
	return result

    def remainder():
	return input[i._:]

    def advance():
	i._ += 1

    def skip_whitespace():
	while True:
	    while token().isspace():
		advance()
	    if token() != ';':
		break
	    t = token()
	    while t != '\n' and t != eof:
		advance()
		t = token()

    def read():
	skip_whitespace()
	t = token()
	if t == "'":
	    advance()
	    return ('quote', read(),)
	elif t == '(':
	    advance()
	    result = []
	    while True:
		skip_whitespace()
		t = token()
		if t == ')':
		    advance()
		    break
		if t == eof:
		    raise 'Incomplete list'
		element = read()
		result.append(element)
	    return tuple(result)
	elif t == eof:
	    return eof
	else:
	    return read_atom()

    def read_atom():
	t = token()
	chars = []
	while t != eof and not t.isspace() and t not in '()':
	    chars.append(t)
	    advance()
	    t = token()
        return intern(''.join(chars))

    while True:
        x = read()
        if x == eof:
            break
        yield x


# Writing s-expressions

def write(sexpr):
    if isinstance(sexpr, tuple):
	return '(%s)' % ' '.join(map(write, sexpr))
    if isinstance(sexpr, basestring):
        return sexpr
    return repr(sexpr)
