from atexit import register
from cheese.pipeline.iterable_dataset import IterablePipeline, InvalidDataException
from cheese.data import BatchElement
from cheese.client.gradio_client import GradioFront

from cheese import CHEESE

from dataclasses import dataclass

from PIL import Image
from cheese.utils.img_utils import url2img

import gradio as gr
import datasets
import time

"""
    In this example task, we present two images from the laion-art dataset to our labellers,
    and have them select which one they prefer over the two. For the case in which an image
    is not loading for them, they will be given an error button to specify they are not seeing any data.
"""

# BatchElement should store everything you want to write to result dataset
# And everything you want to show the labeller
# Ensure every field has a default value

# Note that BatchElements have several parameters, so use keywords when calling
# constructor on your own BatchElement
@dataclass
class ImageSelectionBatchElement(BatchElement):
    img1_url : str = None
    img2_url : str = None
    select : int = 0 # 0 None, -1 Left, 1, Right
    time : float = 0 # Time in seconds it took for user to select image

class ImageSelectionPipeline(IterablePipeline):
    def preprocess(self, x):
        """
        Preprocess is called as soon as a new data element is drawn from iterator.
        """
        return x["URL"]
    
    def fetch(self) -> ImageSelectionBatchElement:
        """
        Fetch is meant to draw the next piece of data from the data source and construct a BatchElement
        out of it.
        """
        # IterablePipeline.fetch_next gets the next item from iterator and preprocesses it
        # It will return None if it could not get any new items
        url1 = self.fetch_next()
        url2 = self.fetch_next()
        
        res = ImageSelectionBatchElement(img1_url = url1, img2_url = url2)
        return res
    
    def post(self, be : ImageSelectionBatchElement):
        """
        Post takes a finished (labelled) batch element and posts it to result dataset.
        """
        row = {"img1_url" : be.img1_url, "img2_url" : be.img2_url, "selection" : be.select, "time" : be.time}
        # IterablePipeline.post_row(...) takes a dict and adds it as a row to end of the result dataset
        # It also saves the result dataset and updates progress (in most cases it should always be called in post)
        # We check for bad data and avoid it
        if not be.error: self.post_row(row)

# IterablePipeline requires you to convert whatever dataset/data source you want to read from
# into an iterable
def make_iter():
    """
    Make iterator from LAION art dataset (laion/laion-art) parquet file
    """
    ds = datasets.load_dataset("laion/laion-art")
    ds = ds["train"].shuffle()

    return iter(ds)

# The Front object is what will be responsible for showing data to the labeller and collecting their responses
class ImageSelectionFront(GradioFront):

    # main() is where you create your UI
    def main(self):

        # All GradioFronts have one main method you must use:
        # self.response, which is the method called to handle inputs/outputs going between Gradio and CHEESE
        # The first two arguments to response are always assumed to be client's id and taks they are currently working on

        with gr.Column():
            gr.Textbox("Of the two images below, select whichever one you prefer over the other.",
                show_label = False, interactive = False
            )
            error_btn = gr.Button("Press This If An Image Is Not Loading")
            error_btn.style(full_width = True)
            with gr.Row():
                with gr.Column():
                    im_left = gr.Image(show_label = False, shape = (256, 256))
                    btn_left = gr.Button("Select Above")
                    btn_left.style(full_width = True)
                with gr.Column():
                    im_right = gr.Image(show_label = False, shape = (256, 256))
                    btn_right = gr.Button("Select Above")
                    btn_right.style(full_width = True)

        # Note how all button clicks call response, but with different arguments
        # The arguments to response will later be passed to self.receive(...)
        # The result of response is whatever is outputted by self.send()

        # Also note that in all instances, id and task are the first two arguments.
        # Moreover, they must be the first two arguments in ANY function called by a gradio event
        def btn_left_click(id, task):
            return self.response(id, task, "Left")

        def btn_right_click(id, task):
            return self.response(id, task, "Right")

        def error_click(id, task):
            return self.response(id, task, "Error")
        
        # All gradio events must composed with self.wrap_event to ensure id and task are passed properly
        def register_click_event(object, fn):
            self.wrap_event(object.click)(
                fn, inputs = [], outputs = [im_left, im_right]
            )

        register_click_event(btn_left, btn_left_click)
        register_click_event(btn_right, btn_right_click)
        register_click_event(error_btn, error_click)
    
        # Return gradio outputs
        return [im_left, im_right]

    # Response calls receive and passes along id, task and whatever input it got
    # We can use task.data to access the actual data that is being labelled
    # and update it using the users response
    def receive(self, *inp):
        _, task, res = inp

        if res == "Left":
            task.data.select = -1
        elif res == "Right":
            task.data.select = 1
        else:
            task.data.error = True
        
        return task
    
    # Response finally calls present to create outputs for gradio to show user
    # In this example, this is simply the next left and right image
    def present(self, task):
        data : ImageSelectionBatchElement = task.data
        return [data.img1_url, data.img2_url]

if __name__ == "__main__":
    # The pipeline kwargs are inherited from IterablePipeline
    cheese = CHEESE(
        ImageSelectionPipeline, ImageSelectionFront,
        pipeline_kwargs = {
            "iter" : make_iter(), "write_path" : "./img_dataset_res", "force_new" : True, "max_length" : 5
        }
    )

    print("Waiting on client...")
    cheese.start_listening(verbose = True)