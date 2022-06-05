from backend.client import Client
from backend.tasks import Task, TaskType
from backend.client.states import ClientState as CS

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super(Client, self).__init__(self.id)

        self.waiting = False # Waiting on frontend

        self.json_buffer = None

    def handle_task(self) -> bool:

        # Can only handle a task if we have one
        assert self.task is not None

        if not self.waiting:
            # Create JSON payload from the information in the task that will be presentable to the user

            data = {}

            data['story'] = self.task.data.text
            data['caption_index'] = self.task.data.caption_index
            data['captions'] = self.task.data.captions

            self.send_json(data)
            self.waiting = True
        
            return False
        elif self.json_buffer is not None:
            # user is done and wants to send caption back
            data = self.json_buffer
            self.json_buffer = None

            self.task.data.story = data['story']
            self.task.data.caption_index = data['caption_index']
            self.task.data.captions = data['captions']

            self.task.receiver = TaskType.PIPELINE
            self.task.sender = TaskType.USER

            # We have everything we need, no longer busy or waiting
            # Ready to send finished task back to orchestrator
            self.waiting = False
            self.json_buffer = None
            self.state = CS.IDLE

            return True
        else:
            return False

    def send_json(self, data):
        # TODO
        pass

    def receive_json(self, data):
        # TODO 
        self.json_buffer = data
        
        

    

