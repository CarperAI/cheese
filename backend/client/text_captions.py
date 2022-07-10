from backend.client import Client
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.data.text_captions import TextCaptionBatchElement

import gradio as gr

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super().__init__(id)

        self.front = None

    def push_task(self, task : Task):
        try:
            assert self.front is not None
        except:
            raise Exception("Error: Pushed task to frontend before it was initialized")
        
        self.task = task
        data : TextCaptionBatchElement = task.data
        self.front.update(data)

    def init_front(self) -> str:
        self.front = TextCaptionFront()
        self.front.client = self

        return self.front.url

    def front_ping(self):
        """
        For frontend to ping client that it is done with task.
        """
        # First update task data
        self.task.data = self.front.data
        self.notify() 
        
class TextCaptionFront:
    def __init__(self):
        # Set default data and create the UI
        self.demo = gr.Interface(
            fn = self.response,
            inputs = ["text"],
            outputs = [gr.Textbox(placeholder = "")],
        )
        _, local_url, url = self.demo.launch(
            share = True, quiet = True,
            prevent_thread_lock = True,
            )

        self.local = local_url
        self.url = url

        self.data : TextCaptionBatchElement = None
        self.buffer : TextCaptionBatchElement = None
        self.showing_data = False # is data visible?
        # A reference to the owner client object
        self.client = None

    def update(self, data):
        self.buffer = data

    def generate_str(self):
        # generate a string from data using caption indexes
        res = self.data.text

        i = len(self.data.captions) - 1
        for inds in reversed(self.data.caption_index):
            res = res[:inds[0]] + f"[{i}][" + res[inds[0]:inds[1]] + "]" + res[inds[1]:]
            i -= 1

        res_captions = ""
        for i, caption in enumerate(self.data.captions):
            res_captions += f"{i}: {caption}\n"

        return res, res_captions

    def response(self, inp):
        """
        What to display to user after they've pressed submit button.
        """
        if self.showing_data:
            # If they were seeing data and pressed button,
            # we assume they made captions and are now submitting

            # Parse input line by line
            lines = inp.split("\n")
            # First two integers are character positions for caption
            indices = [[int(x) for x in line.split(" ")[:2]] \
                        for line in lines]
            
            # rest is caption
            captions = [" ".join(line.split(" ")[2:]) for line in lines]

            self.data.captions += captions
            self.data.caption_index += indices

            self.showing_data = False
            self.client.front_ping()
            self.data = None
        else:
            # Otherwise if they pressed submit while seeing nothing,
            # they need to be shown their new task
            # If its ready, show it

            if self.buffer is not None:
                self.data = self.buffer
                self.buffer = None
            if self.data is not None:
                self.showing_data = True
                return self.data.text
        return ""


