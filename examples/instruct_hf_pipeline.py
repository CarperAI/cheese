"""
    This example does an instruct type annotation task in which labellers are given
    multiple prompt completions and asked to rank them in order of preference.
    It collects and write a dataset of preferences for completions.
"""

from dataclasses import dataclass
from typing import List, Iterable

from transformers import pipeline
import gradio as gr
from cheese.pipeline.generative import GenerativePipeline
from cheese.models import BaseModel
from cheese.data import BatchElement
from cheese.client.gradio_client import GradioFront
from cheese import CHEESE

@dataclass
class LMGenerationElement(BatchElement):
    query : str = None
    completions : List[str] = None
    rankings : List[int] = None # Ordering for the completions w.r.t indices

class LMPipeline(GenerativePipeline):
    """
    Pipeline for doing language model generation.

    :param n_samples: Number of samples to generate for each query. Due to issues with how gradio registers button events,
    this had to be hardcoded in the demo, so be aware of this if you want to change the value (i.e. add/remove buttons)
    :type n_samples: int

    :param device: Device to use for inference (any n > -1 uses cuda device n, -1 uses cpu). Defaults to 0.
    :type device: int

    :param kwargs: Keyword arguments to pass to GenerativePipeline
    :type kwargs: dict
    """
    def __init__(self, n_samples = 5, device : int = 0, **kwargs):
        super().__init__(**kwargs)

        self.n_samples = n_samples
        self.pipe = pipeline(task="text-generation", model = 'gpt2')
        self.pipe.tokenizer.pad_token_id = self.pipe.model.config.eos_token_id
        

        self.init_buffer()

    def generate(self, model_input : Iterable[str]) -> List[LMGenerationElement]:
        """
        Generates a batch of elements using the pipeline's iterator.
        """
        print("Generate called")
        elements = []
        for i in range(self.batch_size):
            query = model_input[i]
            completions = self.pipe(query, max_length=100, num_return_sequences=self.n_samples)
            completions = [completion["generated_text"][len(query):] for completion in completions]
            elements.append(LMGenerationElement(query=query, completions=completions))
        return elements
    
    def extract_data(self, batch_element : LMGenerationElement) -> dict:
        """
        Extracts data from a batch element.
        """
        return {
            "query" : batch_element.query,
            "completions" : batch_element.completions,
            "rankings" : batch_element.rankings
        }
    
def make_iter(length : int = 20, chunk_size : int = 16, device : int = 0):
    """
        Creates an iterator that generates prompts for the completions that will be presented to labeller.

        :param length: Number of prompts to generate
        :type length: int

        :param chunk_size: Number of prompts to generate in one forward pass
        :type chunk_size: int

        :param device: Device to run model on (any n > -1 uses cuda device n, -1 uses cpu)
        :type device: int
    """
    print("Creating prompt iterator...")
    pipe = pipeline(task="text-generation", model = 'gpt2', device = device)
    pipe.tokenizer.pad_token_id = pipe.model.config.eos_token_id
    chunk_size = 16
    meta_prompt = f"As an example, below is a list of {chunk_size + 3} prompts you could feed to a language model:\n"+\
    "\"What is the capital of France?\"\n"+\
    "\"Write a story about geese\"\n"+\
    "\"Tell me a fun fact about rabbits\"\n" 

    def extract_prompts(entire_generation : str):
        generation = entire_generation[len(meta_prompt):]
        prompts = generation.split("\n")
        prompts = [prompt[1:-1] for prompt in prompts] # Remove quotes
        return prompts[:chunk_size]

    prompt_buffer = []

    while len(prompt_buffer) < length:
        prompts = pipe(meta_prompt, max_length=128, num_return_sequences=chunk_size)
        prompts = sum([extract_prompts(prompt["generated_text"]) for prompt in prompts], [])
        prompt_buffer += prompts
    
    del pipe

    return iter(prompt_buffer)

class LMFront(GradioFront):
    def main(self):
        pressed = gr.State([])
        with gr.Column():
            gr.Button("On the left you will see a prompt. On the right you will "+ \
                "see various possible completions. Select the completions in order of "+ \
                "best to worst", interactive = False, show_label = False)
            with gr.Row():
                query = gr.Textbox("Prompt", interactive = False, show_label = False)
                with gr.Column():
                    gr.Textbox("Completions:", interactive = False, show_label = False)

                    completions = [gr.Button("", interactive = True) for _ in range(5)]
                    

            submit = gr.Button("Submit")
        
        # When a button is pressed, append index to state, and make button not visible

        def press_button(i, pressed_val):
            pressed_val.append(i)

            updates = [gr.update(visible = False if j in pressed_val else True) for j in range(5)]

            return [pressed_val] + updates
        
        def press_btn_1(pressed_val):
            return press_button(0, pressed_val)
        
        def press_btn_2(pressed_val):
            return press_button(1, pressed_val)
        
        def press_btn_3(pressed_val):
            return press_button(2, pressed_val)
        
        def press_btn_4(pressed_val):
            return press_button(3, pressed_val)
        
        def press_btn_5(pressed_val):
            return press_button(4, pressed_val)

        completions[0].click(
            press_btn_1,
            inputs = [pressed],
            outputs = [pressed] + completions
        )
        
        completions[1].click(
            press_btn_2,
            inputs = [pressed],
            outputs = [pressed] + completions
        )

        completions[2].click(
            press_btn_3,
            inputs = [pressed],
            outputs = [pressed] + completions
        )

        completions[3].click(
            press_btn_4,
            inputs = [pressed],
            outputs = [pressed] + completions
        )

        completions[4].click(
            press_btn_5,
            inputs = [pressed],
            outputs = [pressed] + completions
        )

        # When submit is pressed, run response, reset state, and set all buttons to visible

        self.wrap_event(submit.click)(
            self.response, inputs = [pressed], outputs = [pressed, query] + completions
        )

        return [pressed, query] + completions
    
    def receive(self, *inp):
        _, task, pressed_vals = inp
        task.rankings = pressed_vals

        return task
    
    def present(self, task):
        data : LMGenerationElement = task.data

        updates = [gr.update(value = data.completions[i], visible = True) for i in range(5)]
        return [[], data.query] + updates

if __name__ == "__main__":
    write_path = "./rankings_dataset"
    cheese = CHEESE(
        LMPipeline,
        LMFront,
        pipeline_kwargs = {
            "iterator" : make_iter(),
            "write_path" : write_path,
            "max_length" : 20,
            "buffer_size" : 20,
            "batch_size" : 20,
            "force_new" : True,
            "log_progress" : True
        },
        gradio = True
    )

    print(cheese.launch())

    print(cheese.create_client(1))
