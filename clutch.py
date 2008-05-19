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
