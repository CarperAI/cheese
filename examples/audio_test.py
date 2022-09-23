from cheese.pipeline.wav_folder import WavFolderPipeline
from cheese.data import BatchElement
from cheese.client.gradio_client import GradioFront

from cheese.api import CHEESE

from datasets import Dataset
import gradio as gr
from dataclasses import dataclass

"""
    In this example task, we present our labellers with an audio sample and have them rate it as well
    as provide an arbitrary comment on it.
"""

@dataclass
class AudioRatingBatchElement(BatchElement):
    id : int = None # To store index over local data folder, we add ID to elements
    path : str = None
    rating : int = -1
    comment : str = ""

class AudioRatingPipeline(WavFolderPipeline):
    """
    Pipeline for rating audio samples from a folder of WAV files. 
    """

    def init_dataset(self) -> Dataset:
        """
        We initialize our target dataset to store index, path, rating and comments
        """
        return self.init_dataset_from_col_names(["id", "path", "rating", "comment"])

    def fetch(self) -> AudioRatingBatchElement:
        """
        Pops an ID from a queue over the index book, then creates a batch element from corresponding value
        """
        # WavFolderPipeline.id_pop() returns an index and path to a wavfile in the read directory
        return AudioRatingBatchElement(**self.id_pop())

    def post(self, be : AudioRatingBatchElement):
        """
        Post labelled data to result dataset
        """

        if be.error:
            return

        new_row = {"id" : be.id, "file_name" : be.path, "rating" : be.rating, "comment" : be.comment}
        # WavFolderPipeline.id_complete(...) is needed to mark a wav file as having been used so it is not presented again
        # It also saves the dataset and index book, so should be called to post new data in most cases
        self.id_complete(be.id, new_row)

class AudioRatingFront(GradioFront):
    def main(self):
        with gr.Row():
            with gr.Column():
                error_btn = gr.Button("Press this if there is no audio sample being presented.")
                gr.Textbox(
                    "Please provide feedback on the presented audio sample in the form of a rating and comment.",
                    show_label = False, interactive = False
                )
                rating = gr.Slider(
                    minimum = 0, maximum = 10,
                    step = 1, value = 0, label = "Rating"
                )
                comment = gr.Textbox(
                    label = "Comment"
                )
                submit = gr.Button(
                    "Submit"
                )
            with gr.Column():
                sample = gr.Audio(interactive = False, label = "Audio Sample")

        def error_fn(id, task, rating, comment):
            task.data.error = True
            return self.response(id, task, rating, comment)
        
        self.wrap_event(submit.click)(
            self.response, inputs = [rating, comment], outputs = [sample]
        )

        self.wrap_event(error_btn.click)(
            error_fn, inputs = [rating, comment], outputs = [sample]
        )

        return [sample]
    
    def receive(self, *inp):
        """
        Take list of inputs and modify task data with users ratings + comments
        """
        _, task, slider_out, comment = inp
        task.data.rating = slider_out
        task.data.comment = comment

        return task
    
    def present(self, task):
        """
        Extract gradio output (Audio path in this case) from task.data (BatchElement)
        """
        return [task.data.path]

import time
from datasets import load_from_disk

if __name__ == "__main__":
    cheese = CHEESE(
        AudioRatingPipeline, client_cls = AudioRatingFront,
        pipeline_kwargs = {"read_path" : "audio_dataset", "write_path" : "audio_data_res", "force_new" : True}
    )
    print(cheese.launch())

    usr1, pass1 = cheese.create_client(1)
    print(usr1, pass1)

    while True:
        time.sleep(2)
        if cheese.finished:
            print("Done")
            break
    
    res_dataset = load_from_disk("audio_data_res")
    print(res_dataset["file_name"])
    print(res_dataset["rating"])
    print(res_dataset["comment"])
