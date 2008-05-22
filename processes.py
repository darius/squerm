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
    state   = Box(initial_state)
    mailbox = Mailbox()
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
                opt_keeper.send(failure) # XXX
    def to_accept(message, run_queue):
        # XXX a stopped process should drop messages immediately
        was_runnable = state._.is_runnable()
        mailbox.put(message)
        if not was_runnable:
            run_queue.enqueue(process)
    def to_receive(k):
        new_state = WaitingState(mailbox, k)
        if new_state.is_runnable():
            return new_state.step()
        return new_state
    def to___repr__():
        return '#<process %x>' % id(process)
    process = Clutch(locals())
    return process

class SenderClass(Clutch):
    pass

def Sender(process, run_queue):
    def to_send(message):
        process.accept(message, run_queue)
    def to_call(args, k):
        (message,) = args
        to_send(message)
        return RunningState(None, k)        
    def to___repr__():
        return '#<! %r>' % process
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

def WaitingState(mailbox, k):
    def to_is_runnable(): return not mailbox.is_empty()
    def to_step():        return k.step(mailbox.pop())
    def to_trace():       return '<waiting-on %s>' % mailbox
    def to___repr__():    return '<waiting; %r>' % k
    return Clutch(locals())

def StoppedState():
    def to_is_runnable(): return False
    def to_step():        assert False
    def to_trace():       return '<stopped>'
    def to___repr__():    return '<stopped>'
    return Clutch(locals())

def Mailbox():
    messages = []
    def to_is_empty():
        return not messages
    def to_put(message):
        messages.append(message)
    def to_pop():
        return messages.pop(0)  # XXX inefficient
    return Clutch(locals())
