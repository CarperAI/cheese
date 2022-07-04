from typing import ClassVar

from backend.client import ClientManager
import backend.utils as utils

import pika

# Master object for CHEESE
class CHEESEAPI:
    def __init__(self, pipeline_cls, client_cls = None, model_cls = None, pipeline_kwargs = {}, client_kwargs = {}, model_kwargs = {}):
        # Initialize rabbit MQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.msg_channel = self.connection.channel()

        # Create a queue for each receiver
        # Distinction between client/active_client is for 
        # new tasks sent by pipeline vs tasks currently being worked on by client and model together 
        self.msg_channel.queue_declare(queue = "pipeline", exclusive = True)
        self.msg_channel.queue_declare(queue = "client", exclusive = True)
        self.msg_channel.queue_declare(queue = "active", exclusive = True)
        self.msg_channel.queue_declare(queue = "model", exclusive = True)

        # Queue for client manager to message master when it is ready for more data
        self.msg_channel.queue_declare(queue = "main", exclusive = True)
        self.msg_channel.basic_consume(
            queue = 'main',
            auto_ack = True,
            on_message_callback = utils.message_callback(self.client_ping)
        )

        # API components initialized
        self.pipeline = pipeline_cls(**pipeline_kwargs)
        self.model = model_cls(**model_kwargs) if model_cls is not None else None

        self.client_manager = ClientManager()
        self.client_cls = client_cls

        self.pipeline.init_msg_channel(self.msg_channel)
        if self.client is not None: self.client.init_msg_channel(self.msg_channel)
        if self.model is not None: self.model.init_msg_channel(self.msg_channel)

        self.clients = 0
        self.busy_clients = 0


    def __del__(self):
        self.connection.close()
    
    def start(self):
        """
        Begin the loop for collecting data.
        """
        if len(self.client_manager.clients) < 1:
            print("WARNING: No clients were added")

        self.msg_channel.start_consuming()
    
    def client_ping(self, msg):
        """
        Method for ClientManager to ping the API when it needs more tasks or has taken a task
        """

        if msg == utils.msg_constants.SENT:
            # Client sent task to pipeline, needs a new one
            self.busy_clients -= 1
            self.draw()
        if msg == utils.msg_constants.RECEIVED:
            self.busy_clients += 1

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
        else:
            self.pipeline.queue_task()


    

