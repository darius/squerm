import clutch
from primitives import is_bool, is_list, is_string, is_symbol
from symbols import Symbol


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
            return (Symbol('quote'), read(),)
        elif t == ".":
            advance()
            return (Symbol('selector'), read(),)
        elif t == "`":
            advance()
            return (Symbol('quasiquote'), read(),)
        elif t == ",":
            advance()
            t = token()
            if t == "@":
                advance()
                return (Symbol('unquote-splicing'), read(),)
            return (Symbol('unquote'), read(),)
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
                    raise ValueError('Incomplete list')
                element = read()
                result.append(element)
            return tuple(result)
        elif t == eof:
            return eof
        else:
            return read_atom()

    def read_atom():
        t = token()
        if t == '"':
            return read_string()
        if t == '#':
            return read_hash()
        chars = []
        while t != eof and not t.isspace() and t not in '()':
            chars.append(t)
            advance()
            t = token()
        string = ''.join(chars)
        try:
            return int(string)
        except ValueError:
            try:
                return float(string)
            except ValueError:
                return Symbol(string)

    def read_string():
        advance()
        chars = []
        t = token()
        while t != eof and t != '"':
            if t == '\\':
                advance()
                chars.append(read_escape_sequence())
            else:
                chars.append(t)
                advance()
            t = token()
        advance()
        result = ''.join(chars)
        if t == eof:
            raise ValueError('Unterminated string constant: "' + result)
        return result

    escapes = {
        '\\': '\\',
        '\"': '\"',
        'n': '\n',
        'r': '\r',
        # XXX add the rest
        }

    def read_escape_sequence():
        t = token()
        if t in escapes:
            advance()
            return escapes[t]
        elif t == eof:
            raise ValueError('Unterminated string constant')
        else:
            # XXX also do hex escapes, etc.
            raise ValueError('Unknown escape char: ' + t)

    def read_hash():
        advance()
        t = token()
        if t == 't':
            advance()
            return True
        if t == 'f':
            advance()
            return False
        raise ValueError("Bad '#' literal syntax: " + t)

    while True:
        x = read()
        if x == eof:
            break
        yield x


# Writing s-expressions

def write(sexpr):
    if is_list(sexpr):
        return '(%s)' % ' '.join(map(write, sexpr))
    if is_symbol(sexpr):
        return sexpr.get_name() # XXX may need escaping
    if is_string(sexpr):
        return write_string(sexpr)
    if is_bool(sexpr):
        return '#t' if sexpr else '#f'
    return repr(sexpr)

def write_string(s):
    # XXX ugh ugly
    x = repr(s)
    if x.startswith("'"):
        middle = x[1:-1]
        return '"%s"' % middle.replace('"', r'\"')
    return x
