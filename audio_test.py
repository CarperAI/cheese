from backend.pipeline.audio_rating import AudioRatingPipeline
from backend.client.audio_rating import AudioRatingClient
from backend.api import CHEESE

import time
from datasets import load_from_disk

if __name__ == "__main__":
    cheese = CHEESE(
        AudioRatingPipeline, client_cls = AudioRatingClient,
        pipeline_kwargs = {"read_path" : "audio_dataset", "write_path" : "audio_data_res", "force_new" : True}
    )

    url1 = cheese.create_client(1)
    print(url1)

    while True:
        time.sleep(2)
        if cheese.finished:
            print("Done")
            break
    
    res_dataset = load_from_disk("audio_data_res")
    print(res_dataset["file_name"])
    print(res_dataset["rating"])
    print(res_dataset["comment"])