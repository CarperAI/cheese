from abc import abstractmethod

from backend.tasks import Task, TaskType
from backend.client.states import ClientState as CS

class Client:
    def __init__(self, id : int):
        self.id = id
        self.task = None

        self.state = CS.IDLE

    def receive_task(self, task : Task):
        if self.state == CS.BUSY:
            raise Exception("Client was busy")
        self.state = CS.BUSY
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
        if self.state == CS.BUSY:
            return None 
        res = self.task
        self.task = None
        return res

    def is_free(self) -> bool:
        """
        Check if client is free
        """
        return self.state != CS.BUSY

    def is_waiting(self) -> bool:
        """
        Check if client is waiting
        """
        return self.state == CS.WAITING