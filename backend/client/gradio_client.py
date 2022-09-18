from abc import abstractmethod

from typing import Any, Iterable, Dict, Tuple, List, Callable

from backend.data import BatchElement
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.client import ClientManager
import backend.utils.msg_constants as msg_constants
from backend.utils.rabbit_utils import rabbitmq_callback

import pickle
import joblib

from b_rabbit import BRabbit
import gradio as gr
from gradio.components import Component
import time

import random

class GradioClientManager(ClientManager):
    """
    ClientManager for frontends made in Gradio
    """
    def __init__(self):
        # Rabbit connections
        self.publisher = None # to pipeline or model
        self.subscriber = None # get tasks (from pipeline)
        self.subscriber_active = None # get active tasks
    
        # Info on users
        # NOTE: This is just for test purposes and is very barebones,
        # will need to update to something more secure before using in 
        # a setting where security is important
        self.id_pass : Dict[int, int] = {} # [Client ID, Password]
        self.client_ids : Iterable[int] = []

        self.client_tasks : Dict[int, Iterable[Task]]= {} # 
        self.client_states : Dict[int, CS] = {}

        self.front : GradioFront = None

    def init_front(self, front_cls) -> str:
        self.front : GradioFront = front_cls()
        self.front.set_manager(self)
        self.front.launch()
        return self.front.demo.share_url

    def save_user_info(self, path):
        """
        Save info on current users to a file
        """
        joblib.dump(self.id_pass, path)
    
    def load_user_info(self, path):
        """
        Load info on users from a previously saved file
        """
        self.id_pass = joblib.load(path)
        self.client_ids = list(self.id_pass.keys())


    def add_client(self, id : int):
        """
        Add a new client. Creates a user/pass combo.

        :param id: ID for the new client
        """
        if id in self.id_pass:
            raise Exception("Error: Trying to create client with ID that has already been taken")
        
        self.client_tasks[id] = []
        self.client_states[id] = CS.IDLE

        pwd = random.randrange(100000,999999)

        self.id_pass[id] = pwd
        self.client_ids.append(id)

        return id, pwd

    def remove_client(self, id : int):
        del self.client_tasks[id]
        del self.client_states[id]
        del self.id_pass[id]

    def query_client(self, id : int, password : int):
        if id in self.id_pass:
            if self.id_pass[id] == password:
                return True
        return False

    def await_new_task(self, id : int) -> Task:
        """
        GradioFront should call this with ID of client. It will return a new task if one is available. Otherwise,
        it will loop and wait for one.
        
        :param id: ID of the client awaiting a task

        :return: A task, as soon as it is available
        """

        if not id in self.id_pass:
            raise Exception("Awaiting task for ID that is not registered as a client")

        while True:
            if self.client_tasks[id]:
                return self.client_tasks[id].pop(0)
            time.sleep(0.5)
    
    def submit_task(self, id : int, task : Task):
        """
        GradioFront should call this to submit a finished task.

        :param id: ID of the client submitting a task
        
        :param task: The finished task
        """

        self.queue_task(id, task)

    def queue_task(self, id : int, task : Task):
        """
        Given a client id, queues the task that was assigned to that client and marks client as free or active accordingly.
        """

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

        for id in self.client_ids:
            if self.client_states[id] == CS.IDLE:
                self.client_tasks[id].append(task)
                self.client_states[id] = CS.BUSY

                self.publisher.publish(
                    routing_key = 'main',
                    payload = msg_constants.RECEIVED
                )
                return
        
        print("Warning: New task dequeued with no free clients to receive. This is expected if the Rabbit queue was populated before CHEESE was started")
    
    @rabbitmq_callback
    def dequeue_active_task(self, tasks : str):
        """
        Receive message for in progress (active) task. Assumed to be from model
        """
        task : Task = pickle.loads(tasks)

        id = task.client_id

        if id not in self.client_ids:
            raise Exception(f"Error: Active task dequeued but target client with id {id} does not exist")
        if self.client_states[id] != CS.WAITING:
            raise Exception("Error: Active task dequeued but target client was not waiting for any active tasks.")
        
        task.data.trip += 1
        self.client_tasks[id].append(task)
        self.client_states[id] = CS.BUSY

class GradioFront:
    """
    Frontend for CHEESE using Gradio
    """
    def __init__(self):
        self.manager : GradioClientManager = None
        with gr.Blocks() as self.demo:
            self.id : gr.State = gr.Variable(-1)
            self.task : gr.State = gr.Variable(None)

            with gr.Column(visible = True) as login:
                login_comps : Dict[str, Component] = self.login()

            with gr.Column(visible = False) as main:
                outputs = self.main()
            
            # Deal with login here
            def login_fn(id, pwd):
                valid = True
                try:
                    id = int(id.strip())
                    pwd = int(pwd.strip())
                except:
                    valid = False
                
                if valid:
                    valid = self.manager.query_client(id, pwd)
                
                if valid:
                    # When valid, get a task then switch to main screen
                    task = self.manager.await_new_task(id)
                    return [id, task, gr.update(), gr.update(visible = False), gr.update(visible = True)] + \
                        self.present(task)
                else:
                    return [id, None, gr.update(visible = True), gr.update(), gr.update()] + \
                        [None] * len(outputs)
            
            login_comps["submit"].click(
                login_fn,
                inputs = [login_comps["idbox"], login_comps["pwdbox"]],
                outputs = [self.id, self.task, login_comps["error"], login, main] + outputs
            )
    
    def launch(self):
        """
        Launch Gradio demo
        """
        if self.manager is None:
            raise Exception("Error: Tried to lanuch frontend without connecting it to a client manager. Please use GradioFront.set_manager()")
        
        self.demo.launch(
            share = True, quiet = True,
            prevent_thread_lock = True,
            enable_queue = True
        )

    def set_manager(self, manager : GradioClientManager):
        """
        Set the manager for the frontend. This is how it will communicate with backend. Must be set before calling launch
        """
        self.manager = manager
    
    def login(self):
        """
        Returns basic components for login screen
        """
        gr.Textbox("Welcome to CHEESE!", show_label = False, interactive = False).style(rounded = False, border = False)
        idbox = gr.Textbox(label = "User ID", interactive = True)
        pwdbox = gr.Textbox(label = "User Password", interactive = True)
        submit = gr.Button("Submit")
        error = gr.Textbox("Invalid ID or password", visible = False).style(rounded = False, border = False)
        
        return {"idbox" : idbox, "pwdbox" : pwdbox, "submit" : submit, "error" : error}
            
    @abstractmethod
    def main(self) -> List[Component]:
        """
        Gradio interface for collecting data can be written here. Should call GradioFront.response() with
        self. Please read the documentation of GradioFront.response for information on which specific inputs
        and outputs must go to/come out of the function.

        :return: List of all output components in the gradio demo
        """
        pass

    def wrap_event(self, event : Callable):
        """
        For any gradio event (i.e. gr.Button.click, gr.Slider.change),
        wrap with this method to ensure id and task are passed properly.
        """
        return lambda fn, inputs, outputs : event(
            fn, 
            inputs = [self.id, self.task] + inputs,
            outputs = [self.task] + outputs
            )

    @abstractmethod
    def receive(self, *inp) -> Task:
        """
        Receive input from user and modify the data in the task with it.
        Can enforce input validity by raising InvalidInputException.
        Assumes first two parameters in inp are ID and Task respectively.
        
        :return: task modified to reflect user input
        """
        pass

    @abstractmethod
    def present(self, task : Task) -> List[Component]:
        """
        Present data in the task to user. Should take task and return outputs to gradio functions
        in list form
        """
        pass
    
    def response(self, *inp) -> Any:
        """
        Submit input from user then stall until we have an output ready for them.
        Assumes first two parameters in inp are ID and Task respectively

        :param inp: Inputs from gradio components
        
        :return: New task, Outputs to give to gradio components
        """

        client_id : int = inp[0]
        task : Task = None

        try:
            task = self.receive(*inp)
        except Exception as e:
            if type(e) is InvalidInputException:
                return self.handle_input_exception(*e.args)
            else:
                raise e

        self.manager.submit_task(client_id, task)
        task = self.manager.await_new_task(client_id)

        present_out = self.present(task)
        if type(present_out) is tuple: present_out = list(present_out)

        return [task] + present_out
    
    def handle_input_exception(self, *args) -> Any:
        """
        Handle invalid input exceptions. Default behavior is to just present same data again.

        :param *args: List of arguments that caused the exception

        :return: Outputs for gradio demo
        :rtype: Iterable[Any] or Any
        """
        return self.present()

class InvalidInputException(Exception):
    """
    For when input is not valid
    """
    def __init__(self, *args):
        self.args = args
