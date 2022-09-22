from enum import Enum

class ClientState(Enum):
    """
    Possible states for a client.
    """
    IDLE = 0 # Can take a new task
    BUSY = 1 # Handling a task (has sent to frontend)
    WAITING = 2 # Sent task to model, waiting to get it back
