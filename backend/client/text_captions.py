from backend.client import Client

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super(Client, self).__init__(self.id)

        self.waiting = False # waiting for user to send back captions

    def handle_task(self) -> bool:
        assert self.task is not None

        if not self.waiting:
            self.busy = True
            # Create JSON payload from the information in the task that will be presentable to the user

            data = {}

            data['story'] = self.task.data.text
            data['caption_index'] = self.task.data.caption_index
            data['captions'] = self.task.data.captions

            # TODO: Send the json payload to front end
        
            return False
        else:

