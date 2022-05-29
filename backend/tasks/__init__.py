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
    client_id : int = -1 # Once a task has been assigned to client, want to keep track
    model_id : int = -1 # Once a task has been assigned to model, want to keep track