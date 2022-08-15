def runs_in_socket_thread(fn):
    return fn

def synchronized(lock_key):
    def annotation(fn):
        def invoke(self, *args, **kwargs):
            assert hasattr(self, lock_key)
            with getattr(self, lock_key):
                return fn(self, *args, **kwargs)
        return invoke
    return annotation

