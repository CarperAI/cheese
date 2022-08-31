from abc import abstractmethod
import pandas as pd
import os
import joblib
from datasets import load_from_disk, Dataset

import numpy as np

from backend.pipeline import Pipeline
from backend.data import BatchElement
from backend.utils import safe_mkdir

def valid_audio_file(path):
    return path.endswith(".wav")

class WavFolderPipeline(Pipeline):
    """
    Base pipeline for audio datasets in form of directory of .wav files
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

    def save_dataset(self):
        self.res_dataset.save_to_disk(self.write_path)
        joblib.dump(self.index_book, "tmp/index_book.joblib")

    @abstractmethod
    def fetch(self) -> BatchElement:
        """
        Assumes not exhausted. Fetches next BatchElement from data source.
        """
        pass

    @abstractmethod
    def get(self, batch_element : BatchElement):
        """
        Send completed batch element to data destination.
        """
        pass

