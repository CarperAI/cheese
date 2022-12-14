"""
    This test script ensures that datasets can be saved, recovered and saved to again.
"""

from examples.server.image_selection_server import *
from cheese import CHEESE
from dataclasses import dataclass
from datasets import Dataset
import pandas as pd

from b_rabbit import BRabbit

@dataclass
class ImageSelectionBatchElement(BatchElement):
    img1_url : str = None
    img2_url : str = None
    select : int = 0 # 0 None, -1 Left, 1, Right
    time : float = 0 # Time in seconds it took for user to select image

if __name__ == "__main__":
    cheese = CHEESE(
        ImageSelectionPipeline, ImageSelectionFront,
        pipeline_kwargs = {
            "iter" : make_iter(), "write_path" : "./img_dataset_res", "force_new" : True, "max_length" : 5, "format" : "csv"
        }
    )

    # Add something
    data = []

    data.append({
        "img1_url" : "a", "img2_url" : "b",
        "select" : 1, "time" : 1
    })
    cheese.pipeline.post(
        ImageSelectionBatchElement(
            **data[0]
        )
    )

    data.append({
        "img1_url" : "c", "img2_url" : "d",
        "select" : 1, "time" : 1
    })
    cheese.pipeline.post(
        ImageSelectionBatchElement(
            **data[1]
        )
    )

    del cheese

    # Check dataset to make sure the data was saved
    # Assert each row is what we expect
    dataset = pd.read_csv("./img_dataset_res")
    for i in range(len(dataset)):
        assert dataset.loc[i].to_dict() == data[i]

    cheese = CHEESE(    
        ImageSelectionPipeline, ImageSelectionFront,
        pipeline_kwargs = {
            "iter" : make_iter(), "write_path" : "./img_dataset_res", "force_new" : False, "max_length" : 5, "format" : "csv"
        }
    )

    data.append({
        "img1_url" : "e", "img2_url" : "f",
        "select" : 1, "time" : 1
    })
    cheese.pipeline.post(
        ImageSelectionBatchElement(
            **data[2]
        )
    )

    data.append({
        "img1_url" : "g", "img2_url" : "h",
        "select" : 1, "time" : 1
    })
    cheese.pipeline.post(
        ImageSelectionBatchElement(
            **data[3]
        )
    )

    print("==== 2 ====")
    for i in range(len(dataset)):
        assert dataset.loc[i].to_dict() == data[i]

    dataset = pd.read_csv("./img_dataset_res")

    print(" ==== 3 ====")
    for i in range(len(dataset)):
        assert dataset.loc[i].to_dict() == data[i]

    print("All Tests Passed")

