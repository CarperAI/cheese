from typing import Callable

def rabbitmq_callback(fn : Callable):
    """
    Modify function that expects a single string to accept a RabbitMQ message object.
    """

    return lambda self, msg: fn(self, msg.body)