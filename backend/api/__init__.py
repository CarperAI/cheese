from typing import ClassVar

from backend.client import ClientManager

import pika

class CHEESEAPI:
    def __init__(self, pipeline_cls, client_cls = None, model_cls = None, pipeline_kwargs = {}, client_kwargs = {}, model_kwargs = {}):
        # Initialize rabbit MQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.msg_channel = self.connection.channel()

        # Create a queue for each receiver
        # Distinction between client/active_client is for 
        # new tasks sent by pipeline vs tasks currently being worked on by client and model together 
        self.msg_channel.queue_declare(queue = "pipeline")
        self.msg_channel.queue_declare(queue = "client")
        self.msg_channel.queue_declare(queue = "active")
        self.msg_channel.queue_declare(queue = "model")
        
        self.pipeline = pipeline_cls(**pipeline_kwargs)
        self.model = model_cls(**model_kwargs) if model_cls is not None else None

        self.client_manager = ClientManager()
        self.client_cls = client_cls

        self.pipeline.init_msg_channel(self.msg_channel)
        if self.client is not None: self.client.init_msg_channel(self.msg_channel)
        if self.model is not None: self.model.init_msg_channel(self.msg_channel)

    def terminate(self):
        self.connection.close()

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

        return self.client_manager.add_client(id, self.client_cls, **kwargs)
    
    def create_model(self, **kwargs):
        """
        Create instance of model for labelling assistance

        :param kwargs: Any parameters to be passed to the model constructor.
        """
        raise NotImplementedError

    def step(self) -> bool:
        """
        Creates a task from the data pipeline to send to clients, if any clients are free.

        :return: True if task could be sent, false if clients were busy
        """

        # All components receive tasks independently
        # ClientManager sends out tasks based on users
        # All we need to control is when pipeline sends tasks

        free_clients = self.client_manager.get_idle_clients()
        if free_clients > 0:
            self.pipeline.queue_task()
            return True
        else:
            return False


    

