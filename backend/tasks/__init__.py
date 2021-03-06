from dataclasses import dataclass

from backend.data import BatchElement

@dataclass
class Task:
    """
    Task for orchestrator to execute.
    """
    data : BatchElement
    client_id : int = -1 # Once a task has been assigned to client, want to keep track
    model_id : int = -1 # Once a task has been assigned to model, want to keep track
    # For simplicities sake, let -2 denote we are looking for a model
