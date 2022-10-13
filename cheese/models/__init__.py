from abc import abstractmethod
from typing import Iterable, Any

import pickle

from cheese.data import BatchElement
from cheese.tasks import Task

from b_rabbit import BRabbit
from cheese.utils.rabbit_utils import rabbitmq_callback

class BaseModel:
    """
    BaseModel object handles anything that may require a model for processing data. It can also be used more generally
    just to handle data processing separately from the pipeline and client.

    :param batch_size: The maximum number of elements to process at once. If there are not this many elements available,
        the model will simply process everything that is in the task queue.
    :type batch_size: int
    """
    def __init__(self, batch_size : int = 1):
        self.publisher = None
        self.subscriber = None

        self.task_queue = []
        self.working = False # Is task loop running?
    
    def get_stats(self) -> dict:
        """
        Get statistics about the model.
        """
        return {"num_tasks": len(self.task_queue)}

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
    def process(self, data : Iterable[BatchElement]) -> Iterable[BatchElement]:
        """
        Process BatchElement with model. Assume the inputs to the model are in the BatchElement,
        then use them to create some outputs. The outputs should be added to the BatchElement before it is returned.

        :param data: The data to process. Can be an iterable of BatchElements, or a single one, depending on use-case.
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
            tasks = self.task_queue[:self.batch_size]
            self.task_queue = self.task_queue[self.batch_size:]

            data_list = self.process([task.data for task in tasks])
            for i, data in enumerate(data_list):
                tasks[i].data = data
            
            while tasks:
                self.queue_task(tasks[0])
                tasks = tasks[1:]

        self.working = False

    def queue_task(self, task : Task):
        """
        Creates a task and queue to client.
        
        :param task: The task to queue
        :type task: Task
        """
        
        if task.data.trip == task.data.trip_max:
            route = 'pipeline'
        else:
            route = 'active'

        tasks = pickle.dumps(task)
        
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
    
