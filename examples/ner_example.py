from typing import List, Tuple

from cheese.pipeline.iterable_dataset import IterablePipeline, InvalidDataException
from cheese.data import BatchElement
from cheese.client.gradio_client import GradioFront

from cheese.api import CHEESE

from dataclasses import dataclass

from PIL import Image
from cheese.utils.img_utils import url2img

import gradio as gr
import datasets
import time

"""
    In this example task, we show sample text to our labellers, and have them select and label named entities
    within the sample. For this example,we use the wikitext dataset.
"""

@dataclass
class NERBatchElement(BatchElement):
    text : str = None
    entities : List[Tuple[Tuple[int, int], str]] = []
    # For each text, entitis is list of tuples, each tuple is
    # ((start, end), label)

class NERPipeline(IterablePipeline):
    def preprocess(self, x):
        return x["text"]

    def fetch(self) -> NERBatchElement:
        text = self.fetch_next()
        res = NERBatchElement(text = text)
        return res

    def post(self, be : NERBatchElement):
        row = {"text" : be.text, "entities" : be.entities}
        if not be.error: self.post_row(row)

def make_iter():
    """
    Make iterator from wikitext dataset 
    """
    dataset = datasets.load_dataset("wikitext", "wikitext-103-raw-v1")
    return iter(dataset["train"])

class NERFront(GradioFront):
    def main(self):
        with gr.Column():
            text = gr.HighlightedText("")
            btn = gr.Button("Submit")
        
        self.wrap_event(btn.click)(
            self.response, inputs = [text], outputs = [text]
        )

        return [text]

    def receive(self, *inp):
        task = inp[1]
        res = inp[2:]

        # TODO: Gradio can't do HighlightedText as input right now
        return task
    
    def present(self, task):
        data : NERBatchElement = task.data
        entities = data.entities
        
        # for gradio output, turn entities into dictionaries
        ent_dict = [{"entity" : label, "start" : inds[0], "end" : inds[1]} for (inds, label) in entities]
        res = {
            "text" : data.text,
            "entities" : ent_dict
        }
        return [res]

if __name__ == "__main__":
    cheese = CHEESE(
        NERPipeline, NERFront,
        pipeline_kwargs = {
            "iter" : make_iter(),
            "write_path" : "./text_res",
            "force_new" : True,
            "max_length" : 10 # Only show 10 samples before exiting
        }
    )

    print(cheese.launch())

    usr, pwd = cheese.create_client(1)
    print(f"{usr} {pwd}")

    while not cheese.finished:
        time.sleep(1)
    
    print("Done!")
