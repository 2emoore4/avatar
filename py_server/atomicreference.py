import threading

class AtomicReference(object):
    """
    Threadsafe reference guarded by a lock.
    Beware of mutating the data itself.
    """
    def __init__(self, value):
        self._val = value
        self._lock = threading.Lock()

    def get(self, ):
        self._lock.acquire(True)
        value = self._val
        self._lock.release()
        return value

    def set(self, value):
        self._lock.acquire(True)
        self._val = value
        self._lock.release()
