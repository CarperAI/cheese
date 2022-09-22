from dataclasses import dataclass

from backend.data import BatchElement

@dataclass
class Task:
    """
    Tasks to communicate between the components in the backend.

    :param data: The data contained in the task
    :type data: BatchElement

    :param client_id: The ID of the client that is meant to receive this task
    :type client_id: int
    """
    data : BatchElement
    client_id : int = -1
