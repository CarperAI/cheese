from abc import abstractmethod
from typing import List
import copy

import joblib 

from backend.tasks import Task, TaskType
from backend.data import BatchElement
from backend.client import Client

class Orchestrator:
    """
    Abstract class for on orchestrator. Handles moving data between pipeline, humans
    and models that are assisting the labelling process
    """

    def __init__(self):
        self.tasks : List[Task] = []

        # Tasks that are being done by users or a model
        # Example: user shouldn't be getting new data to label
        # if they have sent their current data to the model for assistance
        # Should only get new data once they confirm they are done
        self.active_tasks : List[Task] = []

        # Completed tasks to be delivered to pipeline
        self.done_tasks : List[Task] = []

        self.max_tasks = 10

        self.clients : List[Client] = [] 

        try:
            print("Backup state was found. Load?")
            answer = input("(y/n): ")
            if answer == "y":
                self.restore_state()
        except:
            pass

    # TODO
    def set_client(self, client):
        """
        Sets the client object for the orchestrator.
        """
        self.clients += [client]

    def backup_state(self):
        """
        Backup the current state of the orchestrator.
        """
        joblib.dump(self.tasks, 'tasks.pkl')
    
    def restore_state(self):
        """
        Restore the state of the orchestrator from backup.
        """
        self.tasks = joblib.load('tasks.pkl')

    # TODO
    def is_free(self) -> bool:
        """
        Returns True if can accept more tasks
        """
        if len(self.tasks) < self.max_tasks:
            return True
        return False
    
    def get_completed_tasks(self) -> List[Task]:
        """
        Returns a list of data from completed tasks. Intended to be given directly to Pipeline
        When called, the tasks are deleted from orchestrator.
        """
        res = copy.deepcopy(self.done_tasks)
        self.done_tasks = []
        return res

    @abstractmethod
    def receive_task(self, task : Task):
        """
        Receive a single task
        """
        pass

    def receive_tasks(self, task : List):
        """
        Receive a list of tasks at once
        """
        for t in task:
            self.receive_task(t)

    @abstractmethod
    def handle_task(self):
        """
        Handle the top task in the queue.
        """
        pass

    @abstractmethod 
    def query_clients(self):
        """
        Query the clients for completed tasks
        """
        pass

