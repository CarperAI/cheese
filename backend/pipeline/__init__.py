from abc import abstractmethod
from typing import List

from pyparsing import ParseExpression
from backend.data import BatchElement
from backend.tasks import Task

from b_rabbit import BRabbit

class Pipeline:
    """Abstract base class for a data pipeline. Processes data and communicates with orchestrator"""
    def __init__(self):
        self.publisher = None
        self.subscriber = None

    def init_connection(self, connection : BRabbit):
        """
        Initialize RabbitMQ connection
        """
        self.publisher = connection.EventPublisher(
            b_rabbit = connection,
            publisher_name = 'pipeline'
        )

        self.subscriber = connection.EventSubscriber(
            b_rabbit = connection,
            routing_key = 'pipeline',
            publisher_name = 'client',
            event_listener = self.dequeue_task
        )

        self.subscriber.subscribe_on_thread()

        #self.msg_channel.basic_consume(
        #    queue = 'pipeline',
        #    auto_ack = True,
        #    on_message_callback = rabbit_utils.message_callback(self.dequeue_task)
        #)

    @abstractmethod
    def queue_task(self) -> bool:
        """
        Creates a task and queue to client.
        
        :return: True if succesful, False if pipeline exhausted.
        :rtype: bool
        """
        pass

    @abstractmethod
    def dequeue_task(self, tasks : str):
        """Check inbound queue for completed task."""
        pass