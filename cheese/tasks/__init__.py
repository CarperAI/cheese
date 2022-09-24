from dataclasses import dataclass

from cheese.data import BatchElement

@dataclass
class Task:
    """
    Tasks to communicate between the components in the cheese.

    :param data: The data contained in the task
    :type data: BatchElement

    :param client_id: The ID of the client that is meant to receive this task
    :type client_id: int

    :param terminate: A flag to tell the client to terminate
    :type terminate: bool
    """
    data : BatchElement = None
    client_id : int = -1
    terminate : bool = False
