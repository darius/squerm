from clutch import Clutch, Box


def RunQueue():
    pending_queue = []
    running_process = Box(None)
    def to_enqueue(process):
        if process.is_runnable():
            pending_queue.append(process)
    def to_run():
        while pending_queue:
            running = pending_queue[:]
            del pending_queue[:]
            for process in running:
                running_process._ = process
                process.step()
                to_enqueue(process)
    def to_get_running_process():
        return running_process._
    return Clutch(locals())

def Process(opt_keeper, initial_state):
    state = Box(initial_state)
    def to_is_runnable():
        return state._.is_runnable()
    def to_step():
#        print 'trace:', state._.trace()
        try:
            state._ = state._.step()
        except Exception, e:    # XXX is this the right type to catch?
            failure = Failure(e, process, state._)
            state._ = StoppedState()
            if opt_keeper:
                opt_keeper.send(failure)
    def to___repr__():
        return '#<process %x>' % id(process)
    process = Clutch(locals())
    return process

def WaitingState(choices, k):
    def to_is_runnable():
        return any(receiver.is_ready() for receiver, action in choices)
    def to_step():
        for receiver, action in choices:
            if receiver.is_ready():
                return action.call((receiver.pop(),), k)
        assert False
    def to_trace():
        return '<waiting-on %s>' % choices
    def to___repr__():
        return '<waiting; %r>' % k
    return Clutch(locals())

def sprout(process, run_queue):
    """Return a new receiver/sender pair."""
    receiver = Receiver(process, run_queue)
    return receiver, Sender(receiver)

class ReceiverClass(Clutch): pass
class SenderClass(Clutch): pass

def Receiver(process, run_queue):
    messages = []

    # The first two methods are called only by process in WaitingState:
    def to_is_ready(): return not not messages
    def to_pop():      return messages.pop(0)  # XXX O(len(messages)) time

    # This method is called only by the corresponding sender:
    def to_accept(message):
        # TODO: just drop the message if process has stopped
        was_runnable = process.is_runnable()
        messages.append(message)
        if not was_runnable:
            run_queue.enqueue(process)

    # These are called by the interpreter:
    def to_call(args, k):
        assert () == args
        assert process == run_queue.get_running_process()
        choice = (receiver, identity_fn)
        return WaitingState((choice,), k)
    def to___repr__():
        return '#<? %x %r>' % (id(receiver), process)

    receiver = ReceiverClass(locals())
    return receiver

def Primitive(fn):
    def to_call(args, k):
        return RunningState(fn(*args), k)
    def to___repr__():
        return '#<primitive %s>' % fn.__name__
    return Clutch(locals())

identity_fn = Primitive(lambda x: x)

def Sender(receiver):
    def to_send(message):
        receiver.accept(message)
    def to_call(args, k):
        (message,) = args
        to_send(message)
        return RunningState(None, k)        
    def to___repr__():
        return '#<! %x>' % id(receiver)
    return SenderClass(locals())

def Failure(exception, process, state):
    def to___repr__():
        return '<Failure %r %r %r>' % (exception, process, state)
    return Clutch(locals())

def RunningState(value, k):
    def to_is_runnable(): return True
    def to_step():        return k.step(value)
    def to_trace():       return repr((value, k))
    def to___repr__():    return repr((value, k))
    return Clutch(locals())

def StoppedState():
    def to_is_runnable(): return False
    def to_step():        assert False
    def to_trace():       return '<stopped>'
    def to___repr__():    return '<stopped>'
    return Clutch(locals())
