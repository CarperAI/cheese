from abc import abstractmethod

import pickle

from backend.data import BatchElement
from backend.tasks import Task

from b_rabbit import BRabbit
from backend.utils.rabbit_utils import rabbitmq_callback

class BaseModel:
    def __init__(self):
        self.publisher = None
        self.subscriber = None

        self.task_queue = []
        self.working = False # Is task loop running?

    def init_connection(self, connection : BRabbit):
        """
        Initialize RabbitMQ connection
        """
        self.publisher = connection.EventPublisher(
            b_rabbit = connection,
            publisher_name = 'model'
        )

        self.subscriber = connection.EventSubscriber(
            b_rabbit = connection,
            routing_key = 'model',
            publisher_name = 'client',
            event_listener = self.dequeue_task
        )

        self.subscriber.subscribe_on_thread()

    @abstractmethod
    def process(self, data : BatchElement) -> BatchElement:
        """
        Process BatchElement with model
        """
        pass

    def handle_queued_tasks(self):
        """
        Handle every task in queue. New tasks can be added to queue if needed. Should not be called again if still running.
        """
        if self.working:
            raise Exception("Error: Tried to handle model queue twice after already calling method once.")
        
        self.working = True

        while self.task_queue:
            task = self.task_queue.pop(0)
            task.data = self.process(task)
            self.queue_task(task)

        self.working = False

    def queue_task(self, task : Task):
        """
        Creates a task and queue to client.
        
        :param task: The task to queue
        :type task: Task
        """

        tasks = pickle.dumps(task)
        
        if task.data.trip == task.data.trip_max:
            route = 'pipeline'
        else:
            route = 'active'

        self.publisher.publish(
            routing_key = route,
            payload = tasks
        )
    
    @rabbitmq_callback
    def dequeue_task(self, tasks : str):
        """Check inbound queue for completed task."""
        
        task = pickle.loads(tasks)
        task.data.trip += 1

        self.task_queue.append(task)

        if not self.working:
            self.handle_queued_tasks()
    
