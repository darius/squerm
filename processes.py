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

def Process(initial_state):
    state   = Box(initial_state)
    mailbox = Mailbox()
    def to_is_runnable():
        return state._.is_runnable()
    def to_step():
#        print 'trace:', state._.trace()
        state._ = state._.step()
    def to_accept(message, run_queue):
        # XXX a stopped process should drop messages immediately
        was_runnable = state._.is_runnable()
        mailbox.put(message)
        if not was_runnable:
            run_queue.enqueue(process)
    def to_receive(cont):
        new_state = WaitingState(mailbox, cont)
        if new_state.is_runnable():
            return new_state.step()
        return new_state
    def to___repr__():
        return '#<pid>'
    process = Clutch(locals())
    return process

def RunningState(value, cont):
    def to_is_runnable(): return True
    def to_step():        return cont.step(value)
    def to_trace():       return repr((value, cont))
    return Clutch(locals())

def WaitingState(mailbox, cont):
    def to_is_runnable(): return not mailbox.is_empty()
    def to_step():        return cont.step(mailbox.pop())
    def to_trace():       return '<waiting-on %s>' % mailbox
    return Clutch(locals())

def StoppedState():
    def to_is_runnable(): return False
    def to_step():        assert False
    def to_trace():       return '<stopped>'
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
