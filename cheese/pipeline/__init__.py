from abc import abstractmethod
from typing import List, Dict
import pickle

from pyparsing import ParseExpression
from cheese.data import BatchElement
from cheese.tasks import Task

from b_rabbit import BRabbit
from cheese.utils.rabbit_utils import rabbitmq_callback

class Pipeline:
    """
    Abstract base class for a data pipeline. Processes data by fetching from source of data
    and posting to destination of data
    """
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

        self.model_subscriber = connection.EventSubscriber(
            b_rabbit = connection,
            routing_key = 'pipeline',
            publisher_name = 'model',
            event_listener = self.dequeue_task
        )

        self.subscriber.subscribe_on_thread()
        self.model_subscriber.subscribe_on_thread()
    
    @abstractmethod
    def get_stats(self) -> Dict:
        """
        Returns statistics about pipeline. Likely different for any given Pipeline
        """
        pass

    @abstractmethod
    def exhausted(self) -> bool:
        """
        Is there any more data to read?
        """
        pass

    @abstractmethod
    def fetch(self) -> BatchElement:
        """
        Fetches next BatchElement from data source under assumption it is not exhausted.
        """
        pass

    @abstractmethod
    def post(self, batch_element : BatchElement):
        """
        Post completed batch element to data destination.
        """
        pass

    def queue_task(self) -> bool:
        """
        Creates a task and queue to client.
        
        :return: True if succesful, False if pipeline exhausted.
        :rtype: bool
        """
        
        if self.exhausted():
            return False
        
        batch_element = self.fetch()

        task = Task(batch_element)

        route = 'client' if batch_element.trip_start == "client" else 'model'

        tasks = pickle.dumps(task)

        self.publisher.publish(
            routing_key = route,
            payload = tasks
        )

        return True

    @rabbitmq_callback
    def dequeue_task(self, tasks : str):
        """
        Dequeue a task that has been sent to the pipeline, extract the data inside and post
        to data destination.
        """
        task = pickle.loads(tasks)
        batch_element = task.data

        self.post(batch_element)
