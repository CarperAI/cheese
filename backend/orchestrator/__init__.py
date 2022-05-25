from abc import abstractmethod
from typing import Callable, Dict, Iterable, Tuple
from enum import Enum
from dataclasses import dataclass

from backend.data import BatchElement

class TaskType(Enum):
    """
    Possible recepients/senders for tasks
    """
    PIPELINE = 0
    USER = 1
    MODEL = 2

@dataclass
class Task:
    """
    Task for orchestrator to execute.
    """
    data : BatchElement
    sender : TaskType
    receiver : TaskType 

class Orchestrator:
    """
    Abstract class for on orchestrator. Handles moving data between pipeline, humans
    and models that are assisting the labelling process
    """

    def __init__(self):
        self.tasks = []

    def is_free(self):
        """
        Returns True if there are no tasks in the queue
        """
        return len(self.tasks) == 0

    @abstractmethod
    def receive_from_pipeline(self, data : BatchElement):
        pass