import pandas as pd
import os
import joblib
from datasets import load_from_disk, Dataset

import numpy as np

from backend.pipeline.wav_folder import WavFolderPipeline
from backend.data.audio_rating import AudioRatingBatchElement

class AudioRatingPipeline(WavFolderPipeline):
    """
    Pipeline for rating audio samples from a folder of WAV files. 
    """

    def init_dataset(self) -> Dataset:
        return self.init_dataset_from_col_names(["id", "path", "rating", "comment"])

    def fetch(self) -> AudioRatingBatchElement:
        """
        Pops an ID from a queue over the index book, then creates a batch element from corresponding value
        """
        return AudioRatingBatchElement(**self.id_pop())

    def post(self, batch_element : AudioRatingBatchElement):
        id = batch_element.id
        path = batch_element.path
        rating = batch_element.rating
        comment = batch_element.comment

        new_row = {"id" : id, "file_name" : path, "rating" : rating, "comment" : comment}

        self.id_complete(id, new_row)
