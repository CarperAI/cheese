from cheese.data import BatchElement
from dataclasses import dataclass

@dataclass
class CodeCritiqueElement(BatchElement):
    question : str = None
    answer : str = None
    original_code : str = None
    refined_code : str = None
    critique : str = None

from cheese.pipeline.iterable_dataset import IterablePipeline

class CodeCritiquePipeline(IterablePipeline):
    def preprocess(self, data):
        question = data['body']
        answer = data['answer']['body']
        return {"question": question, "answer": answer}

    def fetch(self) -> CodeCritiqueElement:
        next_element = self.fetch_next()
        # TODO: exit here if no element
        return CodeCritiqueElement(
            question=next_element["question"],
            answer=next_element["answer"],
            original_code=next_element["question"],
            refined_code=next_element["answer"],
            critique=next_element["answer"]
        )

    def post(self, data : CodeCritiqueElement):
        row = {
            "question": data.question,
            "answer": data.answer,
            "original_code": data.original_code,
            "refined_code": data.refined_code,
            "critique": data.critique
        }
        print("posting row: ")
        print(row)
        if not data.error: self.post_row(row)

from cheese.client.gradio_client import GradioFront
import gradio as gr

class CodeCritiqueFront(GradioFront):
    def main(self):
        with gr.Column():
            question = gr.Textbox(interactive = False, label = "Question")
            answer = gr.Textbox(interactive=False, label="Answer")
            original_code = gr.Textbox(interactive=True, label="Extract Original Code From Question")
            refined_code = gr.Textbox(interactive=True, label="Extract Refined Code From Answer")
            critique = gr.Textbox(interactive=True, label="Extract Critique From Answer")
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response,
            inputs = [original_code, refined_code, critique],
            outputs = [question, answer, original_code, refined_code, critique]
        )

        return [question, answer, original_code, refined_code, critique]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, original_code, refined_code, critique = inp
        task.data.original_code = original_code
        task.data.refined_code = refined_code
        task.data.critique = critique
        task.data.error = (original_code is None or refined_code is None or critique is None) # Error if the label wasn't selected

        # We can choose to raise an InvalidInputException here if we want to
        # By default, this would simply result in the same data being shown
        # to the user again.
        # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
        # result dataset

        # Receive has to return the task updated with user input
        return task

    def present(self, task):
        data : CodeCritiqueElement = task.data
        return [data.question, data.answer, data.original_code, data.refined_code, data.critique] # Return list for gradio outputs

import time
from cheese import CHEESE
from datasets import load_dataset

dataset = load_dataset("Dahoas/code-review-instruct-critique-revision-python", split="train")

# dataset = dataset.add_column("python_dataset_index", [0] * len(dataset))
# for index in range(len(dataset)):
#     dataset[index]["python_dataset_index"] = index

data = iter(dataset) # Cast to an iterator for IterablePipeline

cheese = CHEESE(
    pipeline_cls = CodeCritiquePipeline,
    client_cls = CodeCritiqueFront,
    gradio = True,
    pipeline_kwargs = {
        "iter" : data,
        "write_path" : "./code_critique_result.csv",
        "force_new" : False,
        "max_length" : 5
    }
)

print(cheese.launch()) # Prints the URL

for i in range(1, 41):
    print(cheese.create_client(i)) # Create client with ID 1 and return a user/pass for them to use

while not cheese.finished:
    time.sleep(2)

print("Done!")
