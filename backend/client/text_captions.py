from backend.client import Client
from backend.tasks import Task, TaskType

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super(Client, self).__init__(self.id)

        self.waiting = False # waiting for user to send back captions
        self.json_buffer = None

    def handle_task(self) -> bool:
        assert self.task is not None

        if not self.waiting:
            self.busy = True
            # Create JSON payload from the information in the task that will be presentable to the user

            data = {}

            data['story'] = self.task.data.text
            data['caption_index'] = self.task.data.caption_index
            data['captions'] = self.task.data.captions

            self.send_json(data)
        
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

            return True
        else:
            return False

    def send_json(self, data):
        # TODO
        pass

    def receive_json(self, data):
        self.json_buffer = data
        
        

    

