from backend.client.gradio_client import GradioClient, GradioClientFront

import gradio as gr
import numpy as np
import time

default_sound = (44100, np.zeros((44100, 2),dtype = float))

class AudioRatingClient(GradioClient):
    def init_front(self) -> str:
        return super().init_front(AudioRatingFront)

class AudioRatingFront(GradioClientFront):
    def __init__(self):
        super().__init__()

        self.demo = gr.Interface(
            fn = self.response,
            inputs = [
                gr.Slider(minimum = 0, maximum = 10, step = 1, value = 0, label = "Rating"),
                gr.Textbox(label = "Comments")
            ],
            outputs = [gr.Audio(label = "Audio Sample")]
        )
    
    def response(self, *inp):

        if self.showing_data:
            # If they could see audio, we assume that when they're trying to submit now
            slider_out, comment = inp
            
            self.data.rating = slider_out
            self.data.comment = comment
            self.complete_task()

        # Stall until new data is received
        while not self.refresh():
            time.sleep(0.5)
        
        return self.data.path
            
        