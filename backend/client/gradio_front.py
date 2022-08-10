from backend.client import Client, ClientFront
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.data.text_captions import TextCaptionBatchElement

import gradio as gr

class GradioTextCaptionClient(Client):
    def init_front(self) -> str:
        return super().init_front(GradioTextCaptionFront)
        
class GradioTextCaptionFront(ClientFront):
    def __init__(self):
        super().__init__()
        # Set default data and create the UI
        self.demo = gr.Interface(
            fn = self.response,
            inputs = ["text"],
            outputs = [gr.Textbox(placeholder = "")],
        )

    def response(self, inp) -> str:
        """
        Take input from user and gives a response for them to see. If they are being shown a task,
        takes their input as being a caption. Otherwise, ignores the input but refreshes and tries to get a new task.
        """
        if self.showing_data:
            # If they were seeing data and pressed button,
            # we assume they made captions and are now submitting

            # Parse input line by line
            lines = inp.split("\n")
            try:
                # First two integers are character positions for caption
                indices = [[int(x) for x in line.split(" ")[:2]] \
                            for line in lines]
                
                # rest is caption
                captions = [" ".join(line.split(" ")[2:]) for line in lines]
            except:
                return self.data.text + " [Invalid input]"

            self.data.captions += captions
            self.data.caption_index += indices

            self.complete_task()
        else:
            # Otherwise if they pressed submit while seeing nothing,
            # they need to be shown their new task
            # If its ready, show it

            if self.refresh():
                return self.data.text
        return ""

