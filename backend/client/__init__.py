from abc import abstractmethod

from backend.tasks import Task, TaskType

class Client:
    def __init__(self, id : int):
        self.id = id
        self.busy = False
        self.task = None

    def receive_task(self, task : Task):
        if self.busy:
            raise Exception("Client was busy")
        self.busy = True
        self.task = task
    
    @abstractmethod
    def handle_task(self):
        """
        Handle current task.
        """
        pass

    def get_done_task(self) -> Task:
        """
        Get task if it's finished, otherwise returns None
        """
        if self.busy:
            return None 
        res = self.task
        self.task = None
        return res

    def is_free(self) -> bool:
        """
        Check if client is free
        """
        return not self.busy