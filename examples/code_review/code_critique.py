from cheese.data import BatchElement
from dataclasses import dataclass
from cheese.pipeline.iterable_dataset import IterablePipeline
from cheese.client.gradio_client import GradioFront
import gradio as gr

@dataclass
class CodeCritiqueElement(BatchElement):
    question : str = None
    answer : str = None
    critique : str = None
    code : str = None


class CodeCritiquePipeline(IterablePipeline):
    def preprocess(self, x):
        return x  # Probably want to use this step to copy the answer into the code and critique fields

    def fetch(self) -> CodeCritiqueElement:
        next_code_critique_entry = self.fetch_next()
        return CodeCritiqueElement(next_code_critique_entry)

    def post(self, data : CodeCritiqueElement):
        row = {"question": data.question, "answer": data.answer, "critique": data.critique, "code": data.code}
        if not data.error:
            self.post_row(row)


class CodeCritiqueFront(GradioFront):
    def main(self):
        with gr.Column():
            question = gr.Textbox(interactive = False, label = "Text")
            answer = gr.Textbox(interactive=False, label="Text")
            code = gr.Textbox(interactive=True, label="Text")
            critique = gr.Textbox(interactive=True, label="Text")
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response, inputs = [code, critique], outputs = [question, answer]
        )

        return [question, answer]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are the extracted code and critique
        _, task, code, critique = inp
        task.data.code = code
        task.data.critique = critique
        task.data.error = (critique is None or code is None) # Error if the label wasn't selected

        # We can choose to raise an InvalidInputException here if we want to
        # By default, this would simply result in the same data being shown
        # to the user again.
        # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
        # result dataset

        # Receive has to return the task updated with user input
        return task

    def present(self, task):
        data : CodeCritiqueElement = task.data
        return [data.question, data.answer] # Return list for gradio outputs
