from backend.pipeline.text_captions import TextCaptionPipeline
from backend.orchestrator.text_captions import TextCaptionOrchestrator
from backend.client.sim_client import SimClient
from backend.api import CHEESEAPI

from datasets import load_from_disk

if __name__ == "__main__":
    cheese = CHEESEAPI(
        TextCaptionPipeline, TextCaptionOrchestrator, SimClient,
        pipeline_kwargs={"read_path": "dataset", "write_path": "data_res", "force_new": True}
    )

    # Add some simulated clients
    for i in range(2):
        cheese.create_client(i)

    while not cheese.step():
        print(cheese.orch.get_total_tasks())
        pass

    cheese.pipeline.save_dataset()

    # Test to make sure this showed up in the final dataset
    res_dataset = load_from_disk("data_res")
    print(res_dataset["text"])
    print(res_dataset["captions"])
    print(res_dataset["caption_index"])
    print(res_dataset["id"])