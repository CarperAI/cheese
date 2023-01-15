from typing import ClassVar, Iterable, Tuple, Dict, Any, Callable

from cheese.client import ClientManager, ClientStatistics
from cheese.client.gradio_client import GradioClientManager
from cheese.pipeline import Pipeline
from cheese.models import BaseModel

import cheese.utils.msg_constants as msg_constants
from cheese.utils.rabbit_utils import rabbitmq_callback

import pickle
from b_rabbit import BRabbit
from tqdm import tqdm
import time

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

    :param draw_always: If true, doesn't check for free clients before drawing a task.
        This is useful if you are trying to feed data directly to model and don't need to worry about having free clients.
    :type draw_always: bool

    :param host: Host for rabbitmq server. Normally just locahost if you are running locally
    :type host: str

    :param port: Port to run rabbitmq server on
    :type port: int
    """
    def __init__(
        self,
        pipeline_cls = None, client_cls = None, model_cls = None,
        pipeline_kwargs : Dict[str, Any] = {}, model_kwargs : Dict[str, Any] = {},
        gradio : bool = True, draw_always : bool = False,
        host : str = 'localhost', port : int = 5672
        ):

        self.gradio = gradio
        self.draw_always = draw_always

        # Initialize rabbit MQ server
        self.connection = BRabbit(host=host, port=port)

        # Channel for client to notify of task completion
        self.subscriber = self.connection.EventSubscriber(
            b_rabbit = self.connection,
            routing_key = 'main',
            publisher_name = 'client',
            event_listener = self.client_ping
        )

        # Receive tasks via API
        self.api_subscriber = self.connection.EventSubscriber(
            b_rabbit = self.connection,
            routing_key = 'main',
            publisher_name = 'api',
            event_listener = self.api_ping
        )

        # Send data back through API
        self.api_publisher = self.connection.EventPublisher(
            b_rabbit = self.connection,
            publisher_name = 'main'
        )

        self.subscriber.subscribe_on_thread()
        self.api_subscriber.subscribe_on_thread()
        
        # components initialized
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
        self.launched = False

        # Communication with API
        self.receive_buffer = []

        self.url = None

    def launch(self) -> str:
        """
        Launch the frontend and return URL for users to access it.
        """
        if not self.launched:
            url = self.client_manager.init_front(self.client_cls)
        else:
            print("Warning: CHEESE has already been launched")
            return self.url
        
        self.launched = True
        self.url = url
        return url
    
    def start_listening(self, verbose : bool = True, listen_every : float = 1.0):
        """
        If using as a server, call this before running client.

        :param verbose: Whether to print status updates
        :type verbose: bool

        :param run_every: Listen for messages every x seconds
        """

        def send(msg : Any):
            self.api_publisher.publish('api', pickle.dumps(msg))
        
        while True:
            if self.receive_buffer:
                if verbose:
                    print("Received a message", self.receive_buffer[0])
                msg = self.receive_buffer.pop(0).split("|")
                if msg[0] == msg_constants.READY:
                    send(True)
                elif msg[0] == msg_constants.LAUNCH:
                    send(self.launch())
                elif msg[0] == msg_constants.ADD:
                    send(self.create_client(int(msg[1])))
                elif msg[0] == msg_constants.REMOVE:
                    self.remove_client(int(msg[1]))
                elif msg[0] == msg_constants.STATS:
                    send(self.get_stats())
                elif msg[0] == msg_constants.DRAW:
                    self.draw()
                else:
                    print("Warning: Unknown message received", msg)
            time.sleep(listen_every)
        
    @rabbitmq_callback
    def api_ping(self, msg):
        """
        All API calls are routed through this method. Message is parsed to execute some function.
        """
        # Needs:
        # - ready
        # - launch
        # - Create client
        # - Remove client
        # - Get stats
        # - draw

        try:
            self.receive_buffer.append(pickle.loads(msg))
        except Exception as e:
            # Check if the error has to do with receive_buffer not being defined yet
            if "receive_buffer" in str(e):
                print("Warning: RabbitMQ queue non-empty at startup. Consider restarting RabbitMQ server if unexpected errors arise.")


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

        :return: Dictionary containing following statistics and values
            - url: URL for accessing CHEESE frontend
            - finished: Whether pipeline is exhausted
            - num_clients: Number of clients connected to CHEESE
            - num_busy_clients: Number of clients currently working on a task
            - num_tasks: Number of tasks completed overall
            - client_stats: Dictionary of client statistics
            - model_stats: Dictionary of model statistics
            - pipeline_stats: Dictionary of pipeline statistics
        """
        client_stats = self.client_manager.client_statistics

        # Get num_tasks from all clients
        num_tasks = 0
        for client in client_stats:
            stat : ClientStatistics = client_stats[client]
            num_tasks += stat.total_tasks

        return {
            'url' : self.url,
            'finished' : self.finished,
            'num_clients' : self.clients,
            'num_busy_clients' : self.busy_clients,
            'num_tasks' : num_tasks,
            'client_stats' : client_stats,
            'model_stats' : self.model.get_stats() if self.model else None,
            'pipeline_stats' : self.pipeline.get_stats()
        }

    def draw(self):
        """
        Draws a sample from data pipeline and creates a task to send to clients. Does nothing if no free clients.
        This check if overriden if draw_always is set to True.
        """

        if not self.draw_always and self.busy_clients >= self.clients:
            return

        exhausted = not self.pipeline.queue_task()

        if exhausted and self.pipeline.exhausted():
            #  finished, so we can stop
            self.finished = True


    def progress_bar(self, max_tasks : int, access_stat : Callable, call_every : Callable = None, check_every : float = 1.0):
        """
        This function shows a progress bar via tqdm some given stat. Blocks execution.
        Not recommended for interactive use.

        :param max_tasks: The maximum number of tasks to show progress to before returning
        :type max_tasks: int

        :param access_stat: Some callable that returns a stat we want to see progress for (i.e. as an integer).
        :type access_stat: Callable[, int]

        :param call_every: Some callable that we want to call every time stat is updated.
        :type call_every: Callable[, None]

        :param check_every: How often to check for updates to the stat in seconds.
        :type check_every: float
        """

        for i in tqdm(range(max_tasks)):
            current_stat = access_stat()
            while True:
                if call_every: call_every()
                if current_stat != access_stat():
                    break
                time.sleep(check_every)
