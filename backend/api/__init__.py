from typing import ClassVar

from backend.client import ClientManager
import backend.utils.msg_constants as msg_constants
from backend.utils.rabbit_utils import rabbitmq_callback

from b_rabbit import BRabbit

# Master object for CHEESE
class CHEESE:
    def __init__(self, pipeline_cls, client_cls = None, model_cls = None, pipeline_kwargs = {}, client_kwargs = {}, model_kwargs = {}):
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
        self.pipeline = pipeline_cls(**pipeline_kwargs)
        self.model = model_cls(**model_kwargs) if model_cls is not None else None

        self.client_manager = ClientManager()
        self.client_cls = client_cls

        self.pipeline.init_connection(self.connection)
        self.client_manager.init_connection(self.connection)
        if self.model is not None: self.model.init_msg_channel(self.msg_channel)

        self.clients = 0
        self.busy_clients = 0

        self.finished = False # For when pipeline is exhausted
    
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

    def create_client(self, id : int, **kwargs) -> str:
        """
        Create a client instance with given id and any other optional parameters.
        
        :param id: A unique identifying number for the client.
        :type id: int

        :param kwargs: Any other parameters to be passed to the client constructor.

        :return: URL said client can use to access frontend.
        """
        if self.client_cls is None:
            raise Exception("No client class specified")

        res = self.client_manager.add_client(id, self.client_cls, **kwargs)
        self.clients += 1
        self.draw() # pre-emptively draw a task for the client to pick up
        return res
    
    def create_model(self, **kwargs):
        """
        Create instance of model for labelling assistance

        :param kwargs: Any parameters to be passed to the model constructor.
        """
        raise NotImplementedError

    def draw(self):
        """
        Draws a sample from data pipeline and creates a task to send to clients. Does nothing if no free clients.
        """

        if self.busy_clients >= self.clients:
            return

        exhausted = not self.pipeline.queue_task()

        if exhausted and self.pipeline.done:
            #  finished, so we can stop
            self.finished = True


    

