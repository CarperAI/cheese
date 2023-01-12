from cheese.data import BatchElement
from dataclasses import dataclass

@dataclass
class CodeCritiqueElement(BatchElement):
    question : str = None
    answer : str = None
    code : str = None
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
            code=next_element["answer"],
            critique=next_element["answer"]
        )

    def post(self, data : CodeCritiqueElement):
        row = {"question": data.question, "answer": data.answer, "code": data.code, "critique": data.critique}
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
            code = gr.Textbox(interactive=True, label="Code")
            critique = gr.Textbox(interactive=True, label="Critique")
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response, inputs = [code, critique], outputs = [question, answer, code, critique]
        )

        return [question, answer, code, critique]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, code, critique = inp
        task.data.code = code
        task.data.critique = critique
        task.data.error = (code is None or critique is None) # Error if the label wasn't selected

        # We can choose to raise an InvalidInputException here if we want to
        # By default, this would simply result in the same data being shown
        # to the user again.
        # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
        # result dataset

        # Receive has to return the task updated with user input
        return task

    def present(self, task):
        data : CodeCritiqueElement = task.data
        return [data.question, data.answer, data.code, data.critique] # Return list for gradio outputs

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
        "write_path" : "./code_critique_result",
        "force_new" : False,
        "max_length" : 5
    }
)

# For the API to function. More information below.
print("CHEESE is now listening")
cheese.start_listening()

