the_table = {}

class SymbolClass:
    def __init__(self, name):
        assert isinstance(name, basestring), \
            'Symbol name not a string: %r' % name
        self.name = name
    def __repr__(self):
        return self.name
    def get_name(self):
        return self.name

def Symbol(name):
    if name in the_table:
        return the_table[name]
    symbol = SymbolClass(name)
    the_table[name] = symbol
    return symbol
