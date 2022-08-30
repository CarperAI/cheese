import pandas as pd
import os
import joblib
from datasets import load_from_disk, Dataset

from scipy.io.wavfile import read as read_wav
import numpy as np

from backend.pipeline import Pipeline
from backend.data.audio_rating import AudioRatingBatchElement

from backend.utils import safe_mkdir

def valid_audio_file(path):
    return path.endswith(".wav")

class AudioRatingPipeline(Pipeline):
    """
    Pipeline for rating audio samples from a folder of WAV files
    """

    def __init__(self, read_path : str, write_path : str, force_new : bool = False):
        super().__init__()

        self.read_path = read_path
        self.write_path = write_path

        # Assume read path points to directory of wav files
        # Result will be a dataset containing rows of form
        # ([file].wav, rating, comment, more comments...)

        self.total_items = len(os.listdir(self.read_path))
        try:
            assert not force_new
            self.res_dataset = load_from_disk(write_path)
            self.index_book = joblib.load("tmp/index_book.joblib")
        except:
            self.res_dataset = pd.DataFrame(columns = ["id", "file_name", "rating", "comment"])
            self.res_dataset = Dataset.from_pandas(self.res_dataset)
            
            # Objects for keeping track of what data has been processed
            safe_mkdir("tmp")
            self.index_book = {}
            for i, path in enumerate(filter(valid_audio_file, os.listdir(self.read_path))):
                self.index_book[i] = [path, False] # Path and status (i.e. has it been labelled yet)

            self.save_dataset()
        
        # From index book, build queue in terms of ids
        print("Preparing Data Queue")
        self.id_queue = []
        for i in range(self.total_items):
            _, done = self.index_book[i]
            if not done:
                self.id_queue.append(i)

    def exhausted(self) -> bool:
        return not self.id_queue
    
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

    def save_dataset(self):
        self.res_dataset.save_to_disk(self.write_path)
        joblib.dump(self.index_book, "tmp/index_book.joblib")


    