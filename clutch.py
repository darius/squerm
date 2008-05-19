class Clutch:
    """
    A kind of object that can be implemented without self.foo
    and self.bar all over the place.
    """
    def __init__(self, entries):
        self.__dict__.update((key[3:], value) 
                             for key, value in entries.items()
                             if key.startswith('to_'))

class Box:
    def __init__(self, value):
        self._ = value
    def __repr__(self):
        return 'Box(%r)' % self._

class Struct:
    """Create an instance with argument=value slots.
    This is for making a lightweight object whose class doesn't matter."""
    def __init__(self, **entries):
        self.__dict__.update(entries)
    def __cmp__(self, other):
        if isinstance(other, Struct):
            return cmp(self.__dict__, other.__dict__)
        else:
            return cmp(self.__dict__, other)
    def __repr__(self):
        return 'Struct(%s)' % ', '.join('%s=%r' % item 
                                        for item in vars(self).items())

def initialize(entries):
    entries['self'].__dict__.update((key, value) 
                                    for key, value in entries.items()
                                    if key != 'self')
