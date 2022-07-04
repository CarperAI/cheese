from typing import Callable

def message_callback(fn : Callable):
    """
    In Pika, when consumers consume, a callback is called. However, it is passed several arguments irrelevant for
    CHEESE. This decorator takes a function taking only the relevant argument, and allows it to take and drop
    the irrelevant ones Pika gives it.
    """

    return lambda channel, method, properties, body: fn(body)