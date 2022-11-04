from dataclasses import dataclass
from typing import List

from cheese.pipeline.generative import GenerativePipeline
from cheese.models import BaseModel
from cheese.data import BatchElement
from cheese.client.gradio_client import GradioFront
from cheese.api import CHEESE

from PIL import Image

from diffusers import StableDiffusionPipeline
import torch
import numpy as np
import joblib
import random
import gradio as gr
import datasets

import  time

"""
    In this example, we present a number of images from StableDiffusion,
    with prompts generated using a text file of prompts. If you do not wish
    to provide such a text file, it alternatively just uses a single
    generic prompt.
"""

@dataclass
class SDGenerationElement(BatchElement):
    prompt : str = None
    seed : int = None
    img : Image.Image = None
    rating : float = -1
    # The following attributes are important for
    # reproducability if image is not saved
    # Seed and these two attributes are sufficient
    # to reproduce same images
    batch_size : int = 1
    batch_index : int = 0

class SDPipeline(GenerativePipeline):
    """
    Stable Diffusion Pipeline. See GenerativePipeline for all arguments.
    
    :param iterator: Iterator used for prompting generation
    :type iterator: Iterable

    :param sampling_steps: The number of sampling steps to take for each image
    :type sampling_steps: int
    """
    def __init__(self, sampling_steps : int = 10, **kwargs):
        super().__init__(**kwargs)

        # Initialize the pipeline as is normal with diffusers
        self.txt2img_pipeline = StableDiffusionPipeline.from_pretrained(
            "CompVis/stable-diffusion-v1-4",
            use_auth_token = True,
            revision="fp16", 
            torch_dtype=torch.float16,
        ).to('cuda')
        self.txt2img_pipeline.set_progress_bar_config(disable = True)

        self.sampling_steps = sampling_steps

        # Need to always call this with a GenerativePipeline
        # Buffer needs to start filling with generated content
        # to serve to the labellers
        self.init_buffer()
    
    def generate(self, model_input) -> List[SDGenerationElement]:
        """
        Given some input (potentially batched), generate
        a batch of images in the form of a list of data elements
        """
        prompts = model_input
        seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator("cuda").manual_seed(seed)

        imgs = self.txt2img_pipeline(
            prompts,
            num_inference_steps = self.sampling_steps,
            generator = generator,
            batch_size = self.batch_size
        ).images

        return [
            SDGenerationElement(
                prompt = prompts[i],
                seed = seed,
                img = img,
                batch_size = self.batch_size,
                batch_index = i
            ) for i, img in enumerate(imgs)
        ]
    
    def extract_data(self, batch_element : SDGenerationElement) -> dict:
        """
        Turn a batch element into a dict that will be added as row to
        the output dataframe
        """
        return {
            "prompt" : batch_element.prompt,
            "seed" : batch_element.seed,
            "rating" : batch_element.rating,
            "batch_size" : batch_element.batch_size,
            "batch_index" : batch_element.batch_index
        }

def make_iter():
    "Create iterator to feed prompts to SDPipeline"
    try:
        with open("prompts.txt", "r") as f:
            prompts = f.readlines()
        return iter(prompts)
    except:
        return iter(["A beautiful award winning portrait, digital art"] * 20000)

class SDFront(GradioFront):
    """
    The frontend is standard and similar to other CHEESE frontends.
    Please refer to other examples if any details here are unclear.
    """
    def main(self):
        with gr.Row():
            slider = gr.Slider(minimum = 0, maximum = 1, value = 0, label = "Rating")
            with gr.Column():
                img = gr.Image(show_label = False, shape = (224, 224))
                submit = gr.Button(value = "Submit")
        
        self.wrap_event(submit.click)(
            self.response, inputs = [slider], outputs = [img]
        )

        return [img]
    
    def receive(self, *inp):
        _, task, slider = inp

        task.data.rating = slider

        return task
    
    def present(self, task):
        img = task.data.img
        return [img]

if __name__ == "__main__":
    write_path = "./sd_dataset"
    cheese = CHEESE(
        SDPipeline,
        SDFront,
        pipeline_kwargs = {
            "sampling_steps" : 30,
            "iterator" : make_iter(),
            "write_path" : write_path,
            "max_length" : 2000,
            "buffer_size" : 20,
            "batch_size" : 4,
            "force_new" : True,
            "log_progress" : True
        },
        gradio = True
    )

    # We can check buffer to ensure that we only
    # Add clients and launch once pipeline is ready
    # (i.e. the buffer is non empty)
    while not cheese.get_stats()["pipeline_stats"]["buffer_content"] > 0:
        time.sleep(1)

    print(cheese.launch())
    usr, pwd = cheese.create_client(1)
    print(usr, pwd)

    # Label 20 images and show progress bar
    # Progress bar should sync across multiple clients
    cheese.progress_bar(
        max_tasks = 20,
        access_stat = lambda: cheese.get_stats()["pipeline_stats"]["progress"],
    )

    print("Done!")