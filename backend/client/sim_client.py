from backend.tasks import Task, TaskType
from backend.client  import Client
from backend.client.states import ClientState as CS

import random

class SimClient(Client):
    def __init__(self):
        self.id = int(random.random() * 1000)
        super(SimClient, self).__init__(self.id)
    
    def handle_task(self):
        story = self.task.data.text
        caption_inds = []
        captions  = []

        caption_inds = [[0, 5], [4, 7]]
        captions = ["caption 1", "caption 2"]
        
        self.task.data.captions = captions
        self.task.data.caption_index = caption_inds
        self.task.receiver = TaskType.PIPELINE
        self.task.sender = TaskType.USER
        self.state = CS.IDLE