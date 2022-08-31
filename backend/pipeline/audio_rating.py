import pandas as pd
import os
import joblib
from datasets import load_from_disk, Dataset

import numpy as np

from backend.pipeline.wav_folder import WavFolderPipeline
from backend.data.audio_rating import AudioRatingBatchElement

class AudioRatingPipeline(WavFolderPipeline):
    """
    Pipeline for rating audio samples from a folder of WAV files
    """
    def fetch(self) -> AudioRatingBatchElement:
        id = self.id_queue.pop(0)
        path, _ = self.index_book[id]
        path = os.path.join(self.read_path, path)

        be = AudioRatingBatchElement(
            id = id,
            path = path
        )

        return be

    def get(self, batch_element : AudioRatingBatchElement):
        id = batch_element.id
        rating = batch_element.rating
        comment = batch_element.comment

        path, _ = self.index_book[id]
        self.res_dataset = self.res_dataset.add_item(
            {"id" : id, "file_name" : path, "rating" : rating, "comment" : comment}
        )

        self.index_book[id][1] = True

        self.save_dataset()
