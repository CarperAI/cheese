from abc import abstractmethod

from typing import Any, Iterable

from backend.data import BatchElement
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.client import ClientManager
import backend.utils.msg_constants as msg_constants
from backend.utils.rabbit_utils import rabbitmq_callback

import pickle

from b_rabbit import BRabbit
import gradio
from gradio.components import IOComponent
import time

class GradioClient:
    def __init__(self, id : int):
        self.id = id
        self.task : Task = None

        self.manager : ClientManager = None
        self.front : GradioClientFront = None
    
    def set_manager(self, manager : ClientManager):
        self.manager = manager

    def notify(self):
        """
        Notify manager this client has finished task.
        """
        try:
            assert self.manager is not None
        except:
            raise Exception("Error: Trying to notify ClientManager when it was never set")

        self.manager.notify_completion(self.id)
    
    def get_task(self) -> Task:
        """
        Return task and unset it. 
        """
        res = self.task
        self.task = None
        return res
    
    def push_task(self, task : Task):
        """
        Pass a new task to client for it to work on.
        """
        try:
            assert self.front is not None
        except:
            raise Exception("Error: Pushed task to frontend before it was initialized")

        self.task = task
        data : BatchElement = task.data
        self.front.update(data)


    @abstractmethod
    def init_front(self, front_cls = None) -> str:
        """
        Initialize frontend for this particular client and return a URL to access it.
        """
        self.front = front_cls()
        self.front.set_client(self)

        return self.front.launch()

    def front_ping(self):
        """
        For frontend to ping client that it is done with task
        """
        self.task.data = self.front.data
        self.notify()

class GradioClientFront:
    def __init__(self):
        self.demo : gradio.Interface = None
        self.data : BatchElement = None # Data currently being shown to user
        self.buffer : BatchElement = None # Buffer for next data to show user

        self.showing_data = False # is data visible to user currently?
        self.client : GradioClient = None

        self.launched = False

    def make_demo(self, inputs : Iterable[IOComponent], outputs : Iterable[IOComponent]):
        """
        Given a list of inputs and outputs for gradio, constructs demo. Should always be called by a class instance constructor.
        """
        self.demo = gradio.Interface(
            fn = self.response,
            inputs = inputs,
            outputs = outputs
        )

    def set_client(self, parent : GradioClient):
        """
        Set client that is "parent" to this frontend.

        :param parent: Parent of frontend
        :type parent: Client
        """
        self.client = parent
    
    def update(self, data : BatchElement):
        """
        Update the buffer with new data
        """
        self.buffer = data

    def complete_task(self):
        """
        Finish task and wipe data. Ping parent client
        """
        self.showing_data = False
        self.client.front_ping()
        self.data = None
    
    def refresh(self) -> bool:
        """
        Refresh data from buffer.

        :return: Whether or not there is new data to present after the refresh
        :rtype: bool
        """
        if self.buffer is not None:
            self.data = self.buffer
            self.buffer = None
        if self.data is not None:
            self.showing_data = True
            return True
        return False

    def launch(self) -> str:
        """
        Launch the frontend application and return URL to access it

        :return: URL for user to access frontend
        :rtype: str
        """
        try:
            assert self.client is not None
        except:
            raise Exception("Error: Launched frontend with unspecified parent client")

        _, _, url = self.demo.launch(
            share = True, quiet = True,
            prevent_thread_lock = True,
            enable_queue = True
        )
        self.launched = True
        return url

    def response(self, *inp) -> Any:
        """
        Submit input from user then stall until next data is received and ready to display.
        
        :return: Outputs for gradio demo
        :rtype: Iterable[Any] or Any
        """
        if self.showing_data:
            try:
                self.receive(*inp)
            except Exception as e:
                if type(e) is InvalidInputException:
                    return self.handle_input_exception(*e.args)
                else:
                    raise e
                    
            self.complete_task()
        
        # stall until new data ready
        while not self.refresh():
            time.sleep(0.5)
        
        return self.send() 

    def handle_input_exception(self, *args) -> Any:
        """
        Handle invalid input exceptions. Default behavior is to just present same data again.

        :param *args: List of arguments that caused the exception

        :return: Outputs for gradio demo
        :rtype: Iterable[Any] or Any
        """
        return self.send()

    @abstractmethod
    def receive(self, *inp):
        """
        Take input from user and modify self.data in response appropriately.

        :param input: All inputs to the gradio demo
        """
        pass

    @abstractmethod
    def send(self) -> Any:
        """
        Use self.data to send relevant data to user. 

        :return: All outputs to gradio demo
        :rtype: Iterable[any] or any
        """
        pass

class InvalidInputException(Exception):
    """
    For when input is not valid
    """
    def __init__(self, *args):
        self.args = args
