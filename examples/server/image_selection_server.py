from atexit import register
from cheese.pipeline.iterable_dataset import IterablePipeline, InvalidDataException
from cheese.data import BatchElement
from cheese.client.gradio_client import GradioFront

from cheese import CHEESE

from dataclasses import dataclass

from PIL import Image
from cheese.utils.img_utils import url2img

import gradio as gr
import datasets
import time

"""
    In this example task, we present two images from the laion-art dataset to our labellers,
    and have them select which one they prefer over the two. For the case in which an image
    is not loading for them, they will be given an error button to specify they are not seeing any data.
"""

from examples.image_selection import (
    ImageSelectionBatchElement,
    ImageSelectionPipeline,
    make_iter,
    ImageSelectionFront,
)

if __name__ == "__main__":
    # The pipeline kwargs are inherited from IterablePipeline
    cheese = CHEESE(
        ImageSelectionPipeline, ImageSelectionFront,
        pipeline_kwargs = {
            "iter" : make_iter(), "write_path" : "./img_dataset_res", "force_new" : True, "max_length" : 5
        }
    )

    print("Waiting on client...")
    cheese.start_listening()
