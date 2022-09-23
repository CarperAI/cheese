from abc import abstractmethod
from cheese.data import BatchElement

from cheese.tasks import Task
from cheese.client.states import ClientState as CS
import cheese.utils.msg_constants as msg_constants
from cheese.utils.rabbit_utils import rabbitmq_callback

import pickle

from b_rabbit import BRabbit
import gradio as gr

class ClientManager:
    def __init__(self):
        # <id : int, Client>
        self.clients = {}
        # <id : int, ClientState>
        self.client_states = {}

        self.publisher = None # to pipeline or model
        self.subscriber = None # get tasks (from pipeline)
        self.subscriber_active = None # get active tasks
    
    def add_client(self, id : int, client_cls, **kwargs) -> str:
        """
        Add a client to the ClientManager and return a url to the frontend.
        """
        self.clients[id] = client_cls(id, **kwargs)
        self.clients[id].set_manager(self)
        url = self.clients[id].init_front()
        self.client_states[id] = CS.IDLE

        return url
    
    def remove_client(self, id : int):
        """
        Remove a client from the ClientManager. Note: this drops any task that client is working on.
        """
        del self.clients[id]
        del self.client_states[id]

    def get_idle_clients(self) -> int:
        """
        Get count of how many clients are idle.
        """
        cnt = 0
        for key in self.client_states:
            if self.client_states[key] == CS.IDLE:
                cnt += 1
    
    def init_connection(self, connection : BRabbit):
        """
        Initialize message channel and consumption callbacks.
        """

        self.publisher = connection.EventPublisher(
            b_rabbit = connection,
            publisher_name = 'client'
        )

        self.subscriber = connection.EventSubscriber(
            b_rabbit = connection,
            routing_key = 'client',
            publisher_name = 'pipeline',
            event_listener = self.dequeue_task
        )

        self.subscriber_active = connection.EventSubscriber(
            b_rabbit = connection,
            routing_key = 'active',
            publisher_name = 'model',
            event_listener = self.dequeue_active_task
        )

        self.subscriber.subscribe_on_thread()
        self.subscriber_active.subscribe_on_thread()

    def notify_completion(self, id : int):
        """
        Notify the ClientManager that a client has completed a task.
        """
        self.queue_task(id)

    def queue_task(self, id : int):
        """
        Given a client id, queues the task that was assigned to that client and marks client as free or active accordingly.
        """

        task : Task = self.clients[id].get_task()
        task.data.client_id = id
        task.client_id = id

        tasks = pickle.dumps(task)

        to_pipeline = task.data.trip >= task.data.trip_max

        if to_pipeline:
            self.client_states[id] = CS.IDLE

            # Send finished task to pipeline
            self.publisher.publish(
                routing_key = 'pipeline',
                payload = tasks
            )
            
            # Tell main object we are ready for more data
            self.publisher.publish(
                routing_key = 'main',
                payload = msg_constants.SENT
            )
        else: # send to model
            self.client_states[id] = CS.WAITING

            self.publisher.publish(
                routing_key = 'model',
                payload = tasks
            )

    @rabbitmq_callback
    def dequeue_task(self, tasks : str):
        """
        Receive message for a new task. Assume this is from pipeline
        """
        task : Task = pickle.loads(tasks)
        task.data.trip += 1

        for id in self.clients:
            if self.client_states[id] == CS.IDLE:
                self.clients[id].push_task(task)
                self.client_states[id] = CS.BUSY

                self.publisher.publish(
                    routing_key = 'main',
                    payload = msg_constants.RECEIVED
                )
                return
        
        raise Exception("Error: New task dequeued with no free clients to receive.")
    
    @rabbitmq_callback
    def dequeue_active_task(self, tasks : str):
        """
        Receive message for in progress (active) task.
        """
        task : Task = pickle.loads(tasks)

        id = task.client_id

        if id not in self.client_states:
            raise Exception(f"Error: Active task dequeued but target client with id {id} does not exist")
        if self.client_states[id] != CS.WAITING:
            raise Exception("Error: Active task dequeued but target client was not waiting for any active tasks.")
        
        task.data.trip += 1
        self.clients[id].push_task(task)
        self.client_states[id] = CS.BUSY

class Client:
    def __init__(self, id : int):
        self.id = id
        self.task : Task = None

        self.manager : ClientManager = None
        self.front : ClientFront = None
    
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

class ClientFront:
    def __init__(self):
        self.demo : gr.Interface = None
        self.data : BatchElement = None # Data currently being shown to user
        self.buffer : BatchElement = None # Buffer for next data to show user

        self.showing_data = False # is data visible to user currently?
        self.client : Client = None

        self.launched = False

    def set_client(self, parent : Client):
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
        )
        self.launched = True
        return url
