from cheese.api import CHEESE
from cheese.client.gradio_client import GradioFront, InvalidInputException
from cheese.data import BatchElement
from cheese.models import BaseModel
from cheese.pipeline.write_only import WriteOnlyPipeline
from dataclasses import dataclass
from examples.architext.architext_util import prompt_to_layout

import gradio as gr
import json
import random
import pickle
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict


@dataclass
class ArchitextBatchElement(BatchElement):
    prompt : str = ""
    creativity : str = None # Low, Medium, High
    result : Dict = None  # { image: PIL.Image.Image, layout: str, layout_after_removed: str }
    feedback : str = ""
    score : int = 0
    rule : str = None
    rule_score : str = None

    trip_max : int = 3 # data -> client -> model -> client => 3 targets in trip

class ArchitextPipeline(WriteOnlyPipeline):
    def fetch(self) -> ArchitextBatchElement:
        return ArchitextBatchElement()
    
    def post(self, batch_element : ArchitextBatchElement):
        data = batch_element
        self.add_row_to_dataset(
            {
                "prompt" : data.prompt,
                "creativity" : data.creativity,
                "result" : pickle.dumps(data.result),
                "feedback" : data.feedback,
                "score" : int(data.score),
                "rule" : data.rule,
                "rule_score" : data.rule_score
            }
        )


class ArchitextModel(BaseModel):
    def __init__(self):
        super().__init__()

        self.model = AutoModelForCausalLM.from_pretrained("architext/gptj-162M")
        self.tokenizer = AutoTokenizer.from_pretrained("gpt2")

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
    
    def process(self, data: ArchitextBatchElement) -> ArchitextBatchElement:
        imgs_comb, out_dict = prompt_to_layout(self.model, self.tokenizer, self.device, data.prompt, data.creativity)
        data.result = { 'image': imgs_comb, 'layout': out_dict }
        return data


class ArchitextFront(GradioFront):
    rules = [
        "The rooms are appropriately allocated for comfortable living.",
        "The design is structured around a pronounced room.",
        "The design is simple.",
        "The design contains no inaccessible rooms.",
        "The design is plausible.",
        "The design makes sense."
    ]

    def main(self):
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(label = "Prompt")
                creativity = gr.Radio(choices = ["Low", "Medium", "High"], label = "Creativity", value = "Low")
                feedback = gr.Textbox(label = "Feedback on Generation", interactive = False, value = " ")
                rating = gr.Slider(label = "Generation Rating", minimum = 0, maximum = 10, step = 1, interactive = False,  value = 0)
                rule = gr.Textbox(interactive = False, value = " ", visible = False)
                rule_score = gr.Radio(choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"], interactive = False, value = " ")
                spaces_to_remove = gr.CheckboxGroup(label = "Rooms to delete (ordered from top left to bottom right)", interactive = False, value = None, choices=[])

            with gr.Column():
                img = gr.Image(label = "Layout")
                submit = gr.Button("Submit")

        self.wrap_event(submit.click)(
            self.response, 
            inputs = [prompt, creativity, feedback, rating, rule, rule_score, spaces_to_remove],
            outputs = [img, prompt, creativity, feedback, rating, rule, rule_score, spaces_to_remove]
        )
        
        return [img, prompt, creativity, feedback, rating, rule, rule_score, spaces_to_remove]
    
    def receive(self, *inp):
        id, task, *inp = inp
        prompting = task.data.result is None # Must be prompting if no image visible
        if ((inp[0] == "" or inp[1] is None) and prompting) or ((inp[2] == "" or inp[3] is None) and not prompting):
            raise InvalidInputException(*inp)
        task.data.prompt, task.data.creativity, task.data.feedback, task.data.score, task.data.rule, task.data.rule_score, spaces_removed = inp

        spaces_removed = self.space_names_title_case_to_camel_case(spaces_removed)

        if spaces_removed is not None and len(spaces_removed) > 0:
            # Here we want to receive the input from the spaces_to_remove list and map
            # it into a full dict of the result without with keys in spaces_to_remove.
            result_layout_with_removed = {}
            layout_string = task.data.result['layout']
            layout = json.loads(layout_string)

            for space_name in layout.keys():
                result_layout_with_removed[space_name] = layout[space_name]

            for removed_space_name in spaces_removed:
                result_layout_with_removed.pop(removed_space_name, None)

            task.data.result['layout_after_removed'] = json.dumps(result_layout_with_removed)

        return task

    def present(self, task):
        img = None
        space_names = []
        if task.data.result is not None:
            if 'image' in task.data.result.keys():
                img = task.data.result['image']
            if 'layout' in task.data.result.keys():
                layout_string = task.data.result['layout']
                layout = json.loads(layout_string)
                space_names = list(layout.keys())

        if img is None:
            prompt = gr.update(interactive = True)
            creativity = gr.update(interactive = True)
            feedback = gr.update(interactive = False, value = " ", visible = False)
            rating = gr.update(interactive = False, value = 0, visible = False)
            rule = gr.update(interactive = False, visible = False)
            rule_score = gr.update(interactive = False, value = [], visible = False)
            spaces_to_remove = gr.update(interactive = False,
                                         choices = self.space_names_camel_case_to_title_case(space_names),
                                         value = [], visible = False)
        else:
            rule_string = self.rules[random.randint(0, 6)];
            prompt = gr.update(interactive = False)
            creativity = gr.update(interactive = False)
            feedback = gr.update(interactive = True, visible = True)
            rating = gr.update(interactive = True, visible = True)
            rule = gr.update(interactive = False, value = rule_string, visible = False)
            rule_score = gr.update(interactive = True, label = rule_string, visible = True)

            if len(space_names) > 0:
                spaces_to_remove = gr.update(interactive = True,
                                             choices = self.space_names_camel_case_to_title_case(space_names),
                                             visible = True)
            else:
                spaces_to_remove = gr.update(interactive = True,
                                             choices = self.space_names_camel_case_to_title_case(space_names),
                                             value = [], visible = True)

        return [img, prompt, creativity, feedback, rating, rule, rule_score, spaces_to_remove]

    def space_names_title_case_to_camel_case(self, space_names):
        camel_case_space_names = []
        for space_name in space_names:
            space_name = space_name.replace(' ', '_')  # Replace spaces with underscores
            space_name = space_name.lower()  # Convert to lowercase
            camel_case_space_names.append(space_name)
        return camel_case_space_names

    def space_names_camel_case_to_title_case(self, space_names):
        title_case_space_names = []
        for space_name in space_names:
            space_name = space_name.replace('_', ' ')  # Replace underscores with spaces
            space_name = space_name.title()  # Convert to title case
            title_case_space_names.append(space_name)
        return title_case_space_names

if __name__ == "__main__":
    # The pipeline kwargs are inherited from IterablePipeline
    cheese = CHEESE(
        ArchitextPipeline, ArchitextFront, ArchitextModel,
        pipeline_kwargs = {
            "write_path" : "./architext_dataset_res", "force_new" : True
        }
    )
    url = cheese.launch()
    print(url)

    usr, pwd = cheese.create_client(1)
    print(usr, pwd)

    while not cheese.finished:
        time.sleep(2)
    
    print("Done!")
