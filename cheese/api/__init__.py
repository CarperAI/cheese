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
class CHEESEAPI:
    """
    API to access CHEESE master object. Assumes

    :param host: Host for rabbitmq server. Normally just locahost if you are running locally
    :type host: str

    :param port: Port to run rabbitmq server on
    :type port: int

    :param timeout: Timeout for waiting for main server to respond
    :type timeout: float
    """
    def __init__(self, host : str = 'localhost', port : int = 5672, timeout : float = 10):
        self.timeout = timeout

        # Initialize rabbit MQ server
        self.connection = BRabbit(host=host, port=port)

        # Channel to get results back from main server
        self.subscriber = self.connection.EventSubscriber(
            b_rabbit = self.connection,
            routing_key = 'api',
            publisher_name = 'main',
            event_listener = self.main_listener
        )

        self.subscriber.subscribe_on_thread()

        # Channel to send commands to main server
        self.publisher = self.connection.EventPublisher(
            b_rabbit = self.connection,
            publisher_name = 'api'
        )

        # Any received values from main will be placed here
        self.buffer : Any = None 

        # Check if main server is running
        self.connected_to_main : bool = False
        self.publisher.publish('main', pickle.dumps(msg_constants.READY))
        self.connected_to_main = True

        if not self.await_result():
            raise Exception("Main server not running")

    @rabbitmq_callback
    def main_listener(self, msg : str):
        """
        Callback for main server. Receives messages from main server and places them in buffer.
        """
        if not self.connected_to_main:
            print("Warning: RabbitMQ queue non-empty at startup. Consider restarting RabbitMQ server if unexpected errors arise.")
            return
        msg = pickle.loads(msg)
        self.buffer = msg
    
    def await_result(self, time_step : float = 0.5):
        """
        Assuming buffer is none
        """
        total_time = 0
        while self.buffer is None:
            time.sleep(time_step)
            total_time += time_step
            if total_time > self.timeout:
                print("Warning: Timeout exceeded awaiting API result.")
                return None
        
        res = self.buffer
        self.buffer = None
        return res


    def launch(self) -> str:
        """
        Launch the frontend and return URL for users to access it.
        """
        self.publisher.publish('main', pickle.dumps(msg_constants.LAUNCH))
        return self.await_result()
    
    def create_client(self, id : int) -> Tuple[int, int]:
        """
        Create a client instance with given id.
        
        :param id: A unique identifying number for the client.
        :type id: int

        :return: Username and password user can use to log in to CHEESE
        """
        msg = f"{msg_constants.ADD}|{id}"
        self.publisher.publish('main', pickle.dumps(msg))

        return self.await_result()
    
    def remove_client(self, id : int):
        """
        Remove client with given id.

        :param id: A unique identifying number for the client.
        :type id: int
        """
        msg = f"{msg_constants.REMOVE}|{id}"
        self.publisher.publish('main', pickle.dumps(msg))

        return self.await_result()

    def get_stats(self) -> Dict:
        """
        Get various statistics in the form of a dictionary.

        :return: Dictionary containing following statistics:
            - num_clients: Number of clients connected to CHEESE
            - num_busy_clients: Number of clients currently working on a task
            - num_tasks: Number of tasks completed overall
            - client_stats: Dictionary of client statistics
            - model_stats: Dictionary of model statistics
            - pipeline_stats: Dictionary of pipeline statistics
        """
        self.publisher.publish('main', pickle.dumps(msg_constants.STATS))

        return self.await_result()

    def draw(self):
        """
        Draws a sample from data pipeline and creates a task to send to clients. Does nothing if no free clients.
        This check if overriden if draw_always is set to True.
        """
        self.publisher.publish('main', pickle.dumps(msg_constants.DRAW))

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

    

