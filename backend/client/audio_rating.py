from backend.client.gradio_client import GradioClient, GradioClientFront

import gradio as gr

class AudioRatingClient(GradioClient):
    def init_front(self) -> str:
        return super().init_front(AudioRatingFront)

class AudioRatingFront(GradioClientFront):
    def __init__(self):
        super().__init__()

        self.demo = gr.Interface(
            fn = self.response,
            inputs = [gr.Slider(minimum = 0, maximum = 10, step = 1, value = 0), "textbox"],
            outputs = ["audio"]
        )
    
    def response(self, inp):

        if self.showing_data:
            # If they could see audio, we assume that when they're trying to submit now
            slider_out, comment = inp
            print(slider_out, comment)
            
        else:
            if self.refresh():
                return (self.data.sr, self.data.audio)