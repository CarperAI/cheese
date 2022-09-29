from re import I
from typing import ClassVar, Iterable, Tuple, Dict, Any

from cheese.client import ClientManager, ClientStatistics
from cheese.client.gradio_client import GradioClientManager
from cheese.pipeline import Pipeline
from cheese.models import BaseModel

import cheese.utils.msg_constants as msg_constants
from cheese.utils.rabbit_utils import rabbitmq_callback

from b_rabbit import BRabbit

# Master object for CHEESE
class CHEESE:
    """
    Main object to use for running tasks with CHEESE

    :param pipeline_cls: Class for pipeline
    :type pipeline_cls: Callable[, Pipeline]

    :param client_cls: Class for client
    :type client_cls: Callable[,GradioFront] if gradio

    :param model_cls: Class for model
    :type model_cls: Callable[,BaseModel]

    :param pipeline_kwargs: Additional keyword arguments to pass to pipeline constructor
    :type pipeline_kwargs: Dict[str, Any]

    :param gradio: Whether to use gradio or custom frontend
    :type gradio: bool
    """
    def __init__(
        self,
        pipeline_cls, client_cls = None, model_cls = None,
        pipeline_kwargs : Dict[str, Any] = {}, model_kwargs : Dict[str, Any] = {},
        gradio : bool = True
        ):

        self.gradio = gradio

        # Initialize rabbit MQ server
        self.connection = BRabbit(host='localhost', port=5672)

        # Channel for client to notify of task completion
        self.subscriber = self.connection.EventSubscriber(
            b_rabbit = self.connection,
            routing_key = 'main',
            publisher_name = 'client',
            event_listener = self.client_ping
        )

        self.subscriber.subscribe_on_thread()
        
        # API components initialized
        self.pipeline : Pipeline = pipeline_cls(**pipeline_kwargs)
        self.model : BaseModel = model_cls(**model_kwargs) if model_cls is not None else None

        self.client_cls = client_cls
        if gradio:
            self.client_manager = GradioClientManager()
        else:
            self.client_manager = ClientManager()

        self.pipeline.init_connection(self.connection)
        self.client_manager.init_connection(self.connection)
        if self.model is not None: self.model.init_connection(self.connection)

        self.clients = 0
        self.busy_clients = 0

        self.finished = False # For when pipeline is exhausted

    def launch(self) -> str:
        """
        Launch the frontend and return URL for users to access it.
        """
        return self.client_manager.init_front(self.client_cls)
    
    @rabbitmq_callback
    def client_ping(self, msg):
        """
        Method for ClientManager to ping the API when it needs more tasks or has taken a task
        """
        msg = msg.decode('utf-8')
        if msg == msg_constants.SENT:
            # Client sent task to pipeline, needs a new one
            self.busy_clients -= 1
            self.draw()
        elif msg == msg_constants.RECEIVED:
            self.busy_clients += 1
        else:
            raise Exception("Error: Client pinged master with unknown message")

    def create_client(self, id : int) -> Tuple[int, int]:
        """
        Create a client instance with given id.
        
        :param id: A unique identifying number for the client.
        :type id: int

        :return: Username and password user can use to log in to CHEESE
        """

        id, pwd = self.client_manager.add_client(id)
        self.clients += 1
        self.draw() # pre-emptively draw a task for the client to pick up
        return id, pwd
    
    def remove_client(self, id : int):
        """
        Remove client with given id.

        :param id: A unique identifying number for the client.
        :type id: int
        """
        self.client_manager.remove_client(id)
        self.clients -= 1

    def get_stats(self) -> Dict:
        """
        Get various statistics in the form of a dictionary.

        :return: Dictionary containing following statistics:
            - num_clients: Number of clients connected to CHEESE
            - num_busy_clients: Number of clients currently working on a task
            - num_tasks: Number of tasks completed overall
            - client_stats: Dictionary of client statistics
        """
        client_stats = self.client_manager.client_statistics

        # Get num_tasks from all clients
        num_tasks = 0
        for client in client_stats:
            stat : ClientStatistics = client_stats[client]
            num_tasks += stat.total_tasks

        return {
            'num_clients' : self.clients,
            'num_busy_clients' : self.busy_clients,
            'num_tasks' : num_tasks,
            'client_stats' : client_stats
        }
    

    def draw(self):
        """
        Draws a sample from data pipeline and creates a task to send to clients. Does nothing if no free clients.
        """

        if self.busy_clients >= self.clients:
            return

        exhausted = not self.pipeline.queue_task()

        if exhausted and self.pipeline.exhausted():
            #  finished, so we can stop
            self.finished = True


    

