from backend.client import Client
from backend.tasks import Task
from backend.client.states import ClientState as CS

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super(Client, self).__init__(id)

    def push_task(self, task : Task):
        pass

    def init_front(self) -> str:
        pass
        
        

    

