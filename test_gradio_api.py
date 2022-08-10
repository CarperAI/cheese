from backend.pipeline.text_captions import TextCaptionPipeline
from backend.client.gradio_front import GradioTextCaptionClient
from backend.api import CHEESE

from datasets import load_from_disk
import time

if __name__ == "__main__":
    cheese = CHEESE(
        TextCaptionPipeline, client_cls = GradioTextCaptionClient, 
        pipeline_kwargs={"read_path": "dataset", "write_path": "data_res", "force_new": True}
    )

    url1 = cheese.create_client(1)
    print(url1)

    while True:
        time.sleep(2)
        if cheese.finished:
            print("Done")
            break

    # Test to make sure this showed up in the final dataset
    res_dataset = load_from_disk("data_res")
    print(res_dataset["text"])
    print(res_dataset["captions"])
    print(res_dataset["caption_index"])
    print(res_dataset["id"])