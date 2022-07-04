from abc import abstractmethod

from backend.tasks import Task
from backend.client.states import ClientState as CS
import backend.utils as utils

from pika.channel import Channel
import pickle

class ClientManager:
    def __init__(self):
        # <id : int, Client>
        self.clients = {}
        # <id : int, ClientState>
        self.client_states = {}

        self.msg_channel = None
    
    def add_client(self, id : int, client_cls, **kwargs) -> str:
        """
        Add a client to the ClientManager and return a url to the frontend.
        """
        self.clients[id] = client_cls(self, id, **kwargs)
        url = self.clients[id].init_front()
        self.client_states[id] = CS.IDLE

        return url

    def get_idle_clients(self) -> int:
        """
        Get count of how many clients are idle.
        """
        cnt = 0
        for key in self.client_states:
            if self.client_states[key] == CS.IDLE:
                cnt += 1
    
    def init_msg_channel(self, channel : Channel):
        """
        Initialize message channel and consumption callbacks.
        """
        self.msg_channel = channel

        self.msg_channel.basic_consume(
            queue = 'client',
            auto_ack = True,
            on_message_callback = utils.messasge_callback(self.dequeue_task)
        )
        self.msg_channel.basic_consume(
            queue = 'active',
            auto_ack = True,
            on_message_callback = utils.message_callback(self.dequeue_active_task)
        )

    def notify_completion(self, id : int):
        # For frontend client to inform ClientManager of task completion
        self.queue_task(id)

    def queue_task(self, id : int):
        """
        Given a client id, queues the task that was assigned to that client and marks client as free or active accordingly.
        """

        task : Task = self.clients[id].get_task()
        tasks = pickle.dumps(task)

        if task.model_id == -2:
            self.client_states[id] = CS.WAITING
            self.msg_channel.basic_publish(
                exchange = '',
                routing_key = 'model',
                body = tasks
            )
        elif task.model_id == -1:
            self.client_states[id] = CS.IDLE
            self.msg_channel.basic_publish(
                exchange = '',
                routing_key = 'pipeline',
                body = tasks
            )
            self.msg_channel.basic_publish(
                exchange = '',
                routing_key = 'main',
                body = utils.msg_constants.SENT
            )
        else:
            raise Exception("Error: Frontend returned a task with invalid model id parameter.")

    
    def dequeue_task(self, tasks : str):
        """
        Receive message for a new task. Assume this is from pipeline
        """
        task : Task = pickle.load(tasks)

        for id in self.clients:
            if self.client_states[id] == CS.IDLE:
                self.clients[id].push_task(task)
                self.client_states[id] = CS.BUSY

                self.msg_channel.basic_publish(
                    exchange = '',
                    routing_key = 'main',
                    body = utils.msg_constants.RECEIVED
                )
                break
        
        raise Exception("Error: New task dequeued with no free clients to receive.")
    
    def dequeue_active_task(self, tasks : str):
        """
        Receive message for in progress (active) task.
        """
        task : Task = pickle.load(tasks)

        id = task.client_id

        if self.client_states[id] != CS.WAITING:
            raise Exception("Error: Active task dequeued with invalid target client.")
        
        self.clients[id].push_task(task)
        self.client_states[id] = CS.BUSY

class Client:
    def __init__(self, manager : ClientManager, id : int):
        self.id = id
        self.task : Task = None
        self.url : str = None

        self.manager = manager

    def notify(self):
        """
        Notify manager this client has finished task.
        """
        self.manager.notify_completion(self.id)
    
    def get_task(self) -> Task:
        """
        Return task and unset it. 
        """
        res = self.task
        self.task = None
        return res
    
    @abstractmethod
    def push_task(self, task : Task):
        """
        Pass a new task to client for it to work on.
        """
        pass

    @abstractmethod
    def init_front(self) -> str:
        """
        Initialize frontend for this particular client and return a URL to access it.
        """
        pass
