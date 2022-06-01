from backend.client import Client

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super(Client, self).__init__(self.id)

    def handle_task(self):
        # TODO: Implement this
        # Should implement some way of giving the user the text and allowing them to caption it
        
