from typing import Any

from backend.client.gradio_client import GradioClient, GradioClientFront, InvalidInputException
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.data.text_captions import TextCaptionBatchElement

import gradio as gr
import time

class GradioTextCaptionClient(GradioClient):
    def init_front(self) -> str:
        return super().init_front(GradioTextCaptionFront)
        
class GradioTextCaptionFront(GradioClientFront):
    def __init__(self):
        super().__init__()

        self.make_demo(
            inputs = ["text"],
            outputs = [gr.Textbox(placeholder = "")]
        )

    def receive(self, *inp):
        inp = inp[0]
        lines = inp.split("\n")

        # Can check if input is valid (i.e. fits some specifications)
        try:
            # First two integers are character positions for caption
            indices = [[int(x) for x in line.split(" ")[:2]] \
                            for line in lines]
                
            # rest is caption
            captions = [" ".join(line.split(" ")[2:]) for line in lines]
        except:
            raise InvalidInputException(*inp)
        
        self.data.captions += captions
        self.data.caption_index += indices
    
    def send(self):
        return self.data.text

    def handle_input_exception(self, *args) -> Any:
        """
        Handle invalid input by letting user know their output was invalid.
        """
        return super().handle_input_exception(*args) + " [Invalid input]"
