from cheese.data import BatchElement
from dataclasses import dataclass

@dataclass
class PairwiseOfflineElement(BatchElement):
    prompt : str = None
    first_output : str = None
    second_output : str = None
    label : str = None


from cheese.pipeline.iterable_dataset import IterablePipeline

class PairwiseOfflinePipeline(IterablePipeline):
    def preprocess(self, x):
        return x # Don't need any changes here- it's just a string

    def fetch(self) -> PairwiseOfflineElement:
        next_element = self.fetch_next()
        # TODO: exit here if no element
        return PairwiseOfflineElement(
            prompt=next_element["prompt"],
            first_output=next_element["first_output"],
            second_output=next_element["second_output"],
        )

    def post(self, data : PairwiseOfflineElement):
        row = {"prompt": data.prompt, "first_output": data.first_output, "second_output": data.second_output, "label": data.label}
        print("posting row: ")
        print(row)
        if not data.error: self.add_row_to_dataset(row)


from cheese.client.gradio_client import GradioFront
import gradio as gr

class PairwiseOfflineFront(GradioFront):
    def main(self):
        with gr.Column():
            prompt = gr.Textbox(label = "Prompt")
            first_output = gr.Textbox(label = "First response")
            second_output = gr.Textbox(label = "Second response")
            label = gr.Radio(["First", "Second"], label = "Which response do you prefer?", visible = True)
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response, inputs = [label], outputs = [prompt, first_output, second_output, label]
        )

        return [prompt, first_output, second_output, label]

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
        data : PairwiseOfflineElement = task.data
        return [data.prompt, data.first_output, data.second_output, data.label] # Return list for gradio outputs

import csv
from cheese import CHEESE
import time
from datasets import load_dataset

dataset = load_dataset("Dahoas/synthetic-instruct-gptj-pairwise", split="train")
dataset = dataset.rename_column("chosen", "first_output")
dataset = dataset.rename_column("rejected", "second_output")

data = iter(dataset) # Cast to an iterator for IterablePipeline

cheese = CHEESE(
    pipeline_cls = PairwiseOfflinePipeline,
    client_cls = PairwiseOfflineFront,
    gradio = True,
    pipeline_kwargs = {
        "iter" : data,
        "write_path" : "./pairwise_offline_result.csv",
        "force_new" : False
    }
)

print(cheese.launch()) # Prints the URL

with open("./cheese_users.csv", 'r') as data:
    for line in csv.reader(data):
        print(cheese.create_client(int(line[0]), int(line[1])))

while not cheese.finished:
    time.sleep(2)

print("Done!")
