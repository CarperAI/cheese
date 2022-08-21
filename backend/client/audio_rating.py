from backend.client.gradio_client import GradioClient, GradioClientFront

import gradio as gr
import numpy as np
import time

class AudioRatingClient(GradioClient):
    def init_front(self) -> str:
        return super().init_front(AudioRatingFront)

class AudioRatingFront(GradioClientFront):
    def __init__(self):
        super().__init__()

        self.make_demo(
            inputs = [
                gr.Slider(minimum = 0, maximum = 10, step = 1, value = 0, label = "Rating"),
                gr.Textbox(label = "Comments")
            ],
            outputs = [gr.Audio(label = "Audio Sample")]
        )
    
    def receive(self, *inp):
        slider_out, comment = inp
        self.data.rating = slider_out
        self.data.comment = comment
    
    def send(self):
        return self.data.path
            
        