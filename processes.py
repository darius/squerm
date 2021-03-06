import asyncio
import itertools
from clutch import Clutch, Box

def Agenda():
    pending_queue   = []
    running_process = Box(None)
    monitor         = asyncio.Monitor()
    def to_enqueue(process):
        if process.is_runnable():
            pending_queue.append(process)
    def to_run():
        while agenda.has_work():
            agenda.poll()
    def to_has_work():
        return not not pending_queue or monitor.has_work()
    def to_poll():
        agenda.run_pending()
        for reactor in monitor.get_reactors():
            # TODO: we should need to do this only for reactors that
            #  have received demands since the last time through
            reactor.dequeue_demands()
        monitor.poll(0 if pending_queue else None)
    def to_run_pending():
        running = pending_queue[:]
        del pending_queue[:]
        for process in running:
            running_process._ = process
            process.step()
            to_enqueue(process)
    def to_get_running_process():
        return running_process._
    def to_get_monitor():
        return monitor
    agenda = Clutch(locals())
    return agenda

process_ids = itertools.count()

def Process(opt_keeper, initial_state):
    my_id = next(process_ids)
    state = Box(initial_state)
    def to_is_runnable():
        return state._.is_runnable()
    def to_step():
#        print 'trace %x:' % id(process), state._.trace()
        try:
            state._ = state._.step()
            # XXX if we got back a StoppedState, shouldn't we also
            #  send a message to the keeper? Or should the convention
            #  be that you raise a 'NormalExitException' instead of
            #  returning a StoppedState directly? Or what?
        except Exception, e:    # XXX is this the right type to catch?
            failure = Failure(e, process, state._)
            state._ = StoppedState()
            if opt_keeper:
                opt_keeper.send(failure)
    def to___repr__():
        return '#<process %d>' % my_id
    process = Clutch(locals())
    return process

def WaitingState(choices, k):
    def to_is_runnable():
        return any(receiver.is_ready() for receiver, action in choices)
    def to_step():
        # XXX what about fairness?
        for receiver, action in choices:
            if receiver.is_ready():
                return action.call((receiver.pop(),), k)
        assert False, 'WaitingState stepped when not runnable'
    def to_trace():
        return '<waiting-on %r>' % (choices,)
    def to___repr__():
        return '<waiting; %r>' % k
    return Clutch(locals())

def sprout(process, agenda):
    """Return a new receiver/sender pair."""
    receiver = Receiver(process, agenda)
    return receiver, Sender(receiver)

class ReceiverClass(Clutch): pass
class SenderClass(Clutch): pass

def Receiver(process, agenda):
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
            agenda.enqueue(process)

    # These are called by the interpreter:
    def to_call(args, k):
        assert () == args, 'Receiver takes no arguments: %r' % args
        assert process == agenda.get_running_process(), \
            'Receiver %r called from wrong process' % receiver
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
    def to_step():        assert False, 'Stopped process stepped'
    def to_trace():       return '<stopped>'
    def to___repr__():    return '<stopped>'
    return Clutch(locals())
