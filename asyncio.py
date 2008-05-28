# Modeled after asyncore

import errno
import fcntl
import os
import select
import socket


class Monitor:

    def __init__(self):
        self.fd_map = {}

    def register(self, fd, reactor):
        self.fd_map[fd] = reactor
#        print 'register %d' % fd

    def close(self, fd):
        self.fd_map[fd].close()
        self.withdraw(fd)

    def withdraw(self, fd):
        del self.fd_map[fd]
#        print 'withdraw %d' % fd

    def has_work(self):
        return not not self.fd_map

    def get_reactors(self):
        return self.fd_map.values()

    def poll(self, opt_timeout):
#        print 'polling'
        r, w, e = self._prepare()
        if not (r or w or e):
            return
#        print 'selecting'
        try:
            r, w, e = select.select(r, w, e, opt_timeout)
#            print 'got', r, w, e
        except select.error, err:
            if err[0] == errno.EINTR:
                return
            raise
        self._notify(r, w, e)

    def _prepare(self):
        r = []; w = []; e = []
        for fd, reactor in self.fd_map.items():
            is_r = reactor.poll_readable()
            is_w = reactor.poll_writable()
            if is_r:         r.append(fd)
            if is_w:         w.append(fd)
            if is_r or is_w: e.append(fd)
        return r, w, e

    def _notify(self, r, w, e):
        for reactor in self._reactors(r):
            reactor.on_readable()
        for reactor in self._reactors(w):
            reactor.on_writable()
        for reactor in self._reactors(e):
            reactor.on_exceptional()

    def _reactors(self, fds):
        return (self.fd_map[fd] for fd in fds if fd in self.fd_map)


class Reactor:
    def poll_readable(self): return True
    def poll_writable(self): return True
    def on_readable(self): abstract
    def on_writable(self): abstract
    def on_out_of_band(self): abstract
    def close(self): abstract


class ListeningReactor(Reactor):

    def __init__(self, monitor, address, reuse=True, backlog=10):
        self.monitor   = monitor
        self.address   = address
        self.socket    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)
        if reuse:
            try:
                sockopt = self.socket.getsockopt(socket.SOL_SOCKET,
                                                 socket.SO_REUSEADDR)
                self.socket.setsockopt(socket.SOL_SOCKET,
                                       socket.SO_REUSEADDR,
                                       sockopt | 1)
            except socket.error:
                pass
        self.socket.bind(address)
        self.socket.listen(backlog)
        monitor.register(self.socket.fileno(), self)
        self.on_init()

    def on_init(self):
        pass

    def on_readable(self):
        self.on_accept(*self.socket.accept())

    def on_accept(self, connection, address):
        abstract


class SocketStreamReactor(Reactor):

    read_buffer_size = 4096

    def __init__(self, monitor, sock, address, connected):
        self.monitor   = monitor
        self.socket    = sock
        self.address   = address
        self.connected = connected
        sock.setblocking(0)
        monitor.register(sock.fileno(), self)
        self.on_init()
        if connected:
            self.on_connect()

    def on_init(self):
        pass

    def on_readable(self):
        self.ensure_connected()
        data = self.recv(self.read_buffer_size)
        if data:
            self.on_read(data)
        else:
            self.on_close()

    def on_writable(self):
        self.ensure_connected()
        self.on_write()

    def ensure_connected(self):
        if not self.connected:
            self.connected = True
            self.on_connect()

    def on_connect(self):
        pass

    def on_read(self, data):
        abstract

    def on_write(self):
        abstract

    def on_close(self):
        self.monitor.close(self.socket.fileno())

    def close(self):
        self.socket.close()

    def recv(self, nbytes):
        try:
            return self.socket.recv(nbytes)
        except socket.error, why:
            # winsock sometimes throws ENOTCONN
            if why[0] in (errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN):
                return ''
            raise

    def send(self, data):
        try:
            return self.socket.send(data)
        except socket.error, why:
            if why[0] == errno.EWOULDBLOCK:
                return 0
            else:
                raise


class ClientSocketReactor(SocketStreamReactor):

    def __init__(self, monitor, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SocketStreamReactor.__init__(self, monitor, sock, address, False)
        self.connect()

    def connect(self):
        assert not self.connected
        err = self.socket.connect_ex(self.address)
        if err in (errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK):
            return
        if err in (0, errno.EISCONN):
            self.connected = True
            self.on_connect()
        else:
            raise socket.error, (err, errno.errorcode[err])


class FileReactor(Reactor):

    read_buffer_size = 8192

    def __init__(self, monitor, fd):
        self.monitor = monitor
        self.fd      = fd
        old_flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)
        monitor.register(fd, self)

    def on_readable(self):
        data = os.read(self.fd, self.read_buffer_size)
        if data:
            self.on_read(data)
        else:
            self.on_close()

    def on_read(self, data):
        abstract

    def on_close(self):
        self.monitor.close(self.fd)

    def close(self):
        os.close(self.fd)

    def send(self, data):
        return os.write(data)
