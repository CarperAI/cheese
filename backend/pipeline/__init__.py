from abc import abstractmethod
from typing import List

from pyparsing import ParseExpression
from backend.data import BatchElement
from backend.tasks import Task

from pika.channel import Channel

class Pipeline:
    """Abstract base class for a data pipeline. Processes data and communicates with orchestrator"""
    def __init__(self):
        self.msg_channel = None

    def init_msg_channel(self, channel : Channel):
        self.msg_channel = channel
        self.msg_channel.basic_consume(
            queue = 'pipeline',
            auto_ack = True,
            on_message_callback = self.dequeue_task
        )

    @abstractmethod
    def queue_task(self) -> bool:
        """
        Creates a task and queue to client.
        
        :return: True if succesful, False if pipeline exhausted.
        :rtype: bool
        """
        pass

    @abstractmethod
    def dequeue_task(self):
        """Check inbound queue for completed task."""
        pass