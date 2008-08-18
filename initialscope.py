import os
import sys

import asyncio
from clutch     import Box, Clutch
import interpret
import lispio
from primitives import *
from processes  import Primitive, RunningState, Process, ReceiverClass, \
                       Sender, SenderClass, sprout, StoppedState, WaitingState
from scope      import EmptyScope, OuterScope, RecursiveScope, Scope, ScopeClass
from symbols    import Symbol
import syntax


# Primitive procedures

def Apply():
    def to_call(args, k):
        fn, arglist = args
        return fn.call(arglist, k)
    def to___repr__():
        return '#<primitive apply>'
    return Clutch(locals())

def make_selector(method_name):
    if is_symbol(method_name):
        method_name = method_name.get_name()
    assert isinstance(method_name, basestring), \
        'Selector %r not a string or symbol' % method_name
    assert not method_name.startswith('_'), \
        'Attempt to make private selector %r' % method_name
    return Selector(method_name)

# Whitelist of types whose methods preserve capability discipline.
invocable_types = (basestring, frozenset)

tamings = {
    'rsplit':     lambda s, *args: tuple(s.rsplit(*args)),
    'split':      lambda s, *args: tuple(s.split(*args)),
    'splitlines': lambda s, *args: tuple(s.splitlines(*args)),
    }

def Selector(method_name):
    def to_call(args, k):
        object = args[0]
        assert isinstance(object, invocable_types), \
            'Not method-invocable: %r' % object
        arguments = args[1:]
        if method_name in tamings:
            result = tamings[method_name](object, *arguments)
        else:
            result = getattr(object, method_name)(*arguments)
        return RunningState(result, k)
    def to___repr__():
        return '#<selector %s>' % method_name
    return Clutch(locals())

def Eval():
    def to_call(args, k):
        sexpr, scope = args
        assert isinstance(scope, ScopeClass), \
            'Second eval argument must be an environment: %r' % scope
        return syntax.expand_exp(sexpr).eval(scope, k)
    def to___repr__():
        return '#<primitive eval>'
    return Clutch(locals())

def extend_environment(vars, vals, scope):
    assert is_list(vars), \
        'First extend-environment argument must be a list: %r' % vars
    for var in vars:
        assert is_symbol(var), \
            'Non-symbol in extend-environment vars list: %r' % vars
    assert is_list(vals), \
        'Second extend-environment argument must be a list: %r' % vals
    assert len(vars) == len(vals), \
        'Vars and vals are different lengths: %r %r' % (vars, vals)
    return Scope(vars, vals, scope)

def ComplainingKeeper():
    def to_send(message):
        print message
    def to_call(args, k):
        (message,) = args
        to_send(message)
        return RunningState(None, k)
    def to___repr__():
        return '#<! complaining-keeper>'
    return SenderClass(locals())

def Choose():
    def to_call(args, k):
        (choices,) = args
        assert is_list(choices), 'Choices not a list: %r' % choices
        for choice in choices:
            assert is_list(choice) and len(choice) == 2, \
                'Choice not a pair, in %r' % choices
            receiver, fn = choice
            assert isinstance(receiver, ReceiverClass), \
                'Choice receiver wrong type, in %r' % choices
        return WaitingState(choices, k)
    def to___repr__():
        return '#<primitive choose>'
    return Clutch(locals())

def Exit():
    def to_call(args, k):
        if len(args) == 0:
            return StoppedState()
        (plaint,) = args
        raise Exception(plaint)
    def to___repr__():
        return '#<primitive exit>'
    return Clutch(locals())

def make_sealer(name):
    class Envelope:
        def __init__(self, contents):
            self.contents = contents
        def __repr__(self):
            return '#<sealed %s>' % name
    def Sealer():
        def to_call((arg,), k):
            return RunningState(Envelope(arg), k)
        def to___repr__():
            return '#<sealer %s>' % name
        return Clutch(locals())
    def Unsealer():
        def to_call((arg,), k):
            if isinstance(arg, Envelope):
                return RunningState(arg.contents, k)
            raise ValueError('Not a sealed %s' % name)
        def to___repr__():
            return '#<unsealer %s>' % name
        return Clutch(locals())
    def IsSealed():             # TODO: combine with unsealer in one object
        def to_call((arg,), k):
            return RunningState(isinstance(arg, Envelope), k)
        def to___repr__():
            return '#<sealed? %s>' % name
        return Clutch(locals())
    return (Sealer(), Unsealer(), IsSealed())

prims = dict((name, Primitive(fn)) for name, fn in primitives_dict.items())
prims.update({'apply':              Apply(),
              'make-selector':      Primitive(make_selector),
              'eval':               Eval(),
              'None':               None,
              'empty-environment':  EmptyScope(),
              'extend-environment': Primitive(extend_environment),
              'complaining-keeper': ComplainingKeeper(),
              'choose':             Choose(),
              'exit':               Exit(),
              'make-sealer':        Primitive(make_sealer),
              })
prims = dict((Symbol(name), value) for name, value in prims.items())

def RecursiveScopeExpr():
    def to_make_closure(scope): return scope
    def to___repr__():          return '<recursive-scope-expr>'
    return Clutch(locals())

safe_scope = RecursiveScope(zip((Symbol('safe-environment'),),
                                (RecursiveScopeExpr(),)),
                            OuterScope(prims))

def make_universal_scope(agenda):
    return add_process_functions(safe_scope, agenda)

def add_process_functions(enclosing_scope, agenda):
    def spawn(opt_keeper, fn):
        assert opt_keeper is False or isinstance(opt_keeper, SenderClass), \
            'Not a keeper: %r' % opt_keeper
        def SpawningState():
            def to_is_runnable(): return True
            def to_step():        return fn.call((), interpret.FinalK())
            def to_trace():       return '<spawning>'
            def to___repr__():    return '<spawning %r>' % fn
            return Clutch(locals())
        process = Process(opt_keeper, SpawningState())
        agenda.enqueue(process)
        return process
    def sprout_fn():
        return sprout(agenda.get_running_process(), agenda)
    return Scope(map(Symbol, ('spawn', 'sprout')),
                 map(Primitive, (spawn, sprout_fn)),
                 enclosing_scope)


def write_string(s):
    sys.stdout.write(s)

def write(x):
    write_string(lispio.write(x))

def newline():
    write_string('\n')

def print_(x):
    write(x)
    newline()

def make_os_scope(outer_scope, agenda):
    names = 'write-string write newline print system'
    funcs = [write_string, write, newline, print_, os.system]
    return Scope(map(Symbol, names.split() + ['tcp-connect']),
                 map(Primitive, funcs) + [TcpConnect(agenda.get_monitor())],
                 outer_scope)

def TcpConnect(monitor):
    def tcp_connect(sender, address, keeper):
        assert isinstance(sender, SenderClass), \
            'First argument should be a sender'
        assert (is_list(address)
                and len(address) == 2
                and is_string(car(address))
                and is_number(cadr(address))), \
                'Second argument should be a (host port) pair'
        assert isinstance(keeper, SenderClass), \
            'Third argument should be a sender'
        ConnectingReactor(monitor, address, keeper, sender)
        return None
    return Primitive(tcp_connect)

class ConnectingReactor(asyncio.ClientSocketReactor):
    def __init__(self, monitor, address, keeper, sender):
        asyncio.ClientSocketReactor.__init__(self, monitor, address)
        self.keeper = keeper
        self.sender = sender
    def poll_readable(self):
        return False
    def on_connect(self):
        self.monitor.withdraw(self.socket.fileno())
        cr = ConnectedReactor(self.monitor, self.socket, self.address,
                              self.keeper)
        demands_r = ReactorReceiver(cr)
        demands_s = Sender(demands_r)
        self.sender.send(demands_s)
    def on_write(self):
        pass
    def dequeue_demands(self):
        pass

def ReactorReceiver(reactor):
    def to_accept(message):
        reactor.enqueue_demand(message)
    return ReceiverClass(locals())

class ConnectedReactor(asyncio.SocketStreamReactor):

    def __init__(self, monitor, socket, address, keeper):
        asyncio.SocketStreamReactor.__init__(self,
                                             monitor, socket, address, True)
        self.keeper       = keeper
        self.demands      = []
        self.readable     = False
        self.read_k       = None
        self.writable     = False
        self.write_string = None
        self.write_k      = None
        self.write_must_complete = False
        self.write_count  = 0

    def enqueue_demand(self, message):
        self.demands.append(message)

    def dequeue_demands(self):
        # To be called once before monitor.poll()
        while self.demands:
            demand = self.demands[0]
            if not is_list(demand):
                self.exit('Bad message to reactor-receiver')
                break
            if demand == (_close,):
                self.exit()
                break
            elif len(demand) == 3 and demand[0] == _read:
                if self.readable:
                    # We already have a read to handle; put off
                    # remaining messages till the next round.
                    break
                _, n_bytes, k = demand
                if not isinstance(n_bytes, int) or n_bytes <= 0:
                    self.exit('Bad #bytes in read')
                    break
                if not isinstance(k, SenderClass):
                    self.exit('Bad sender in read')
                    break
                self.readable = True
                self.read_buffer_size = n_bytes
                self.read_k = k
                self.demands.pop(0) # XXX inefficient
            elif len(demand) == 3 and demand[0] == _write:
                if self.writable:
                    # We already have a write to perform; for this
                    # subsequent one to make any sense, we must not
                    # do only a partial write on the current one.
                    self.write_must_complete = True
                    break
                _, string, k = demand
                if not isinstance(string, basestring):
                    self.exit('Bad string in write')
                    break
                if not isinstance(k, SenderClass):
                    self.exit('Bad sender in write')
                    break
                self.writable = True
                self.write_string = string
                self.write_k = k
                self.demands.pop(0) # XXX inefficient
            else:
                self.exit('Bad message to reactor-receiver')
                break

    def poll_readable(self):
        return self.readable

    def on_read(self, data):
        self.read_k.send(data)
        self.readable = False
        self.read_k = None

    def poll_writable(self):
        return self.writable

    def on_write(self):
        n = self.send(self.write_string)
        if self.write_must_complete and n < len(self.write_string):
            self.write_string = self.write_string[n:]
            self.write_count += n
        else:
            self.write_k.send(self.write_count + n)
            self.writable     = False
            self.write_string = None
            self.write_k      = None
            self.write_must_complete = False
            self.write_count  = 0

    def exit(self, opt_plaint=None):
        if opt_plaint is not None:
            self.keeper.send(opt_plaint)
        self.on_close()

    def on_close(self):
        if self.read_k is not None:
            self.read_k.send(_eof)
        asyncio.SocketStreamReactor.on_close(self)
        # XXX notify keeper too?

_close, _eof, _read, _write = map(Symbol, 'close eof read write'.split())
