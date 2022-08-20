from abc import abstractmethod
from backend.data import BatchElement

from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.client import ClientManager
import backend.utils.msg_constants as msg_constants
from backend.utils.rabbit_utils import rabbitmq_callback

import pickle

from b_rabbit import BRabbit
import gradio as gr

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
        self.demo : gr.Interface = None
        self.data : BatchElement = None # Data currently being shown to user
        self.buffer : BatchElement = None # Buffer for next data to show user

        self.showing_data = False # is data visible to user currently?
        self.client : GradioClient = None

        self.launched = False

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

    @abstractmethod
    def response(self, inp) -> str:
        """
        Take input from user and gives a response for them to see. If they are being shown a task,
        takes their input as being a caption. Otherwise, ignores the input but refreshes and tries to get a new task.
        Abstract method is a skeleton showing example of required structure.
        """
        if self.showing_data:
            # == Use input to complete task ==

            self.complete_task()
        else:
            # Otherwise if they pressed submit while seeing nothing,
            # they need to be shown their new task
            # If its ready, show it

            if self.refresh():
                return self.data.text
        return ""