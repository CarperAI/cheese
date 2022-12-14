from cheese.data import BatchElement
from dataclasses import dataclass

"""
    This is an example referenced in the docs for CHEESE. It provides a user with text, asks for a sentiment label,
    then has a model also provide a sentiment label.
"""


@dataclass
class SentimentElement(BatchElement):
    text : str = None
    label : str = None
    model_label : str = None
    trip_max : int = 2 # -> Client -> Model -> Pipeline = two targets to visit before going back to pipeline

from cheese.pipeline.iterable_dataset import IterablePipeline

class SentimentPipeline(IterablePipeline):
    def preprocess(self, x):
        return x # Don't need any changes here- it's just a string
    
    def fetch(self) -> SentimentElement:
        return SentimentElement(text=self.fetch_next(), label=None)

    def post(self, data : SentimentElement):
        row = {"text": data.text, "label": data.label, "model_label": data.model_label}
        if not data.error: self.post_row(row)

from cheese.models import BaseModel

from transformers import pipeline

class SentimentModel(BaseModel):
    def __init__(self):
        super().__init__()

        # Use HF Transformers to create a small sentiment analysis pipeline
        self.model = pipeline("sentiment-analysis", model = "nlptown/bert-base-multilingual-uncased-sentiment")

    def process(self, data : SentimentElement) -> SentimentElement:
        txt = data.text
        label = self.model(txt)[0]["label"]
        data.model_label = label
        return data

from cheese.client.gradio_client import GradioFront
import gradio as gr

class SentimentFront(GradioFront):
    def main(self):
        with gr.Column():
            txt = gr.Textbox(interactive = False, label = "Text")
            select = gr.Radio(["Positive", "Negative"], label = "Label")
            btn = gr.Button("Submit")
    
        self.wrap_event(btn.click)(
            self.response, inputs = [select], outputs = [txt]
        )

        return [txt]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, label = inp
        task.data.label = label
        task.data.error = (label is None) # Error if the label wasn't selected

        # We can choose to raise an InvalidInputException here if we want to
        # By default, this would simply result in the same data being shown
        # to the user again.
        # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
        # result dataset

        # Receive has to return the task updated with user input
        return task

    def present(self, task):
        data : SentimentElement = task.data
        return [data.text] # Return list for gradio outputs

from cheese import CHEESE
import time

data = ["The goose went to the store and was very happy", "The goose went to the store and was very sad"]
data = iter(data) # Cast to an iterator for IterablePipeline

cheese = CHEESE(
    pipeline_cls = SentimentPipeline,
    client_cls = SentimentFront,
    model_cls = SentimentModel,
    gradio = True,
    pipeline_kwargs = {
        "iter" : data,
        "write_path" : "./sentiment_result",
        "force_new" : True,
        "max_length" : 5
    }
)

print(cheese.launch()) # Prints the URL

print(cheese.create_client(1)) # Create client with ID 1 and return a user/pass for them to use

while not cheese.finished:
    time.sleep(2)

print("Done!")
