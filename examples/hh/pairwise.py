from cheese.data import BatchElement
from dataclasses import dataclass

@dataclass
class SentimentElement(BatchElement):
    prompt : str = ""
    first_output : str = None
    second_output : str = None
    label : str = None

    trip_max : int = 3

from cheese.pipeline.iterable_dataset import IterablePipeline
from cheese.pipeline.write_only import WriteOnlyPipeline

class SentimentPipeline(WriteOnlyPipeline):
    def preprocess(self, x):
        return x # Don't need any changes here- it's just a string

    def fetch(self) -> SentimentElement:
        return SentimentElement()

    def post(self, data : SentimentElement):
        row = {"prompt": data.prompt, "first_output": data.first_output, "second_output": data.second_output, "label": data.label}
        print("posting row: ")
        print(row)
        if not data.error: self.add_row_to_dataset(row)


from cheese.models import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class SentimentModel(BaseModel):
    def __init__(self):
        super().__init__()

        self.model = AutoModelForCausalLM.from_pretrained("gpt2")
        self.tokenizer = AutoTokenizer.from_pretrained("gpt2")

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

    def process(self, data: 'list[SentimentElement]') -> SentimentElement:
        print("process data")
        print(data)
        model_prompt = data[0].prompt

        input_ids = self.tokenizer(model_prompt, return_tensors='pt').to(self.device)
        first_output = self.model.generate(**input_ids, do_sample=True, top_p=0.9, top_k=50,
                                    eos_token_id=50256, max_length=400)
        first_output = self.tokenizer.batch_decode(first_output, skip_special_tokens=True)
        print("first_output")
        print(first_output)
        data[0].first_output = first_output[0][len(model_prompt):len(first_output[0])]

        second_output = self.model.generate(**input_ids, do_sample=True, top_p=0.9, top_k=50,
                                     eos_token_id=50256, max_length=400)
        second_output = self.tokenizer.batch_decode(second_output, skip_special_tokens=True)

        data[0].second_output = second_output[0][len(model_prompt):len(second_output[0])]
        return [data[0]]


from cheese.client.gradio_client import GradioFront
import gradio as gr

class SentimentFront(GradioFront):
    def main(self):
        with gr.Column():
            prompt = gr.Textbox(label = "Prompt", value="Hello GPT")
            first_output = gr.Textbox(interactive = False, label = "First summary")
            second_output = gr.Textbox(interactive = False, label = "Second summary")
            label = gr.Radio(["First", "Second"], label = "Which summary do you prefer?", visible = True)
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response, inputs = [prompt, label], outputs = [prompt, first_output, second_output, label]
        )

        return [prompt, first_output, second_output, label]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, prompt, label = inp
        task.data.prompt = prompt
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

        print("present")
        print(data.first_output)
        print(data.second_output)

        if data.first_output is None and data.second_output is None:
            print("setting select invisible")
            data.label = gr.update(visible=False)
        else:
            data.label = gr.update(visible=True)
            print("setting select visible")

        return [data.prompt, data.first_output, data.second_output, data.label] # Return list for gradio outputs

from cheese import CHEESE
import time

cheese = CHEESE(
    pipeline_cls = SentimentPipeline,
    client_cls = SentimentFront,
    model_cls = SentimentModel,
    pipeline_kwargs = {
        "write_path" : "./pairwise_result.csv",
        "force_new" : True
    }
)

print(cheese.launch()) # Prints the URL

print(cheese.create_client(1)) # Create client with ID 1 and return a user/pass for them to use
print(cheese.create_client(2))
print(cheese.create_client(3))

while not cheese.finished:
    time.sleep(2)

print("Done!")