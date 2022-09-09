from backend.pipeline.wav_folder import WavFolderPipeline
from backend.data import BatchElement
from backend.client.gradio_client import GradioClient, GradioClientFront

from backend.api import CHEESE

from datasets import Dataset
import gradio as gr
from dataclasses import dataclass

"""
    In this example task, we present our labellers with an audio sample and have them rate it as well
    as provide an arbitrary comment on it.
"""

@dataclass
class AudioRatingBatchElement(BatchElement):
    id : int # To store index over local data folder, we add ID to elements
    path : str
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
        new_row = {"id" : be.id, "file_name" : be.path, "rating" : be.rating, "comment" : be.comment}
        # WavFolderPipeline.id_complete(...) is needed to mark a wav file as having been used so it is not presented again
        # It also saves the dataset and index book, so should be called to post new data in most cases
        self.id_complete(be.id, new_row)

class AudioRatingClient(GradioClient):
    def init_front(self) -> str:
        return super().init_front(AudioRatingFront)

class AudioRatingFront(GradioClientFront):
    def __init__(self):
        super().__init__()

        # When defining a new task, GradioClientFront.data is used to access the BatchElement currently
        # being presented to the user

        # Make a super simple gradio demo that takes ratings, comments and shows an audio sample
        self.make_demo(
            inputs = [
                gr.Slider(minimum = 0, maximum = 10, step = 1, value = 0, label = "Rating"),
                gr.Textbox(label = "Comments")
            ],
            outputs = [gr.Audio(label = "Audio Sample")]
        )
    
    def receive(self, *inp):
        """
        Take list of inputs and modify self.data (BatchElement) with users ratings + comments
        """
        slider_out, comment = inp
        self.data.rating = slider_out
        self.data.comment = comment
    
    def send(self):
        """
        Extract gradio output (Audio path in this case) from self.data (BatchElement)
        """
        return self.data.path

import time
from datasets import load_from_disk

if __name__ == "__main__":
    cheese = CHEESE(
        AudioRatingPipeline, client_cls = AudioRatingClient,
        pipeline_kwargs = {"read_path" : "audio_dataset", "write_path" : "audio_data_res", "force_new" : True}
    )

    url1 = cheese.create_client(1)
    print(url1)

    while True:
        time.sleep(2)
        if cheese.finished:
            print("Done")
            break
    
    res_dataset = load_from_disk("audio_data_res")
    print(res_dataset["file_name"])
    print(res_dataset["rating"])
    print(res_dataset["comment"])
