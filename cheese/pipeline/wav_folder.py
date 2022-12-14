from abc import abstractmethod
from typing import Iterable, Dict, Any

import pandas as pd
import os
import joblib
from datasets import load_from_disk, Dataset

import numpy as np

from cheese.pipeline.datasets import DatasetPipeline
from cheese.data import BatchElement
from cheese.utils import safe_mkdir

def valid_audio_file(path):
    return path.endswith(".wav")

class WavFolderPipeline(DatasetPipeline):
    """
    Base pipeline for audio datasets in form of directory of .wav files.
    Writes to a standard datasets format dataset.

    :param read_path: Path to directory of wav files to read from
    :type read_path: str

    :param write_path: Path to directory to write resulting dataset to
    :type write_path: str

    :param force_new: Whether to force a new dataset (as opposed to recovering saved progress from write_path)
    :type force_new: bool
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
            assert self.load_dataset()
            self.index_book = joblib.load("save_data/index_book.joblib")
        except:
            
            # Objects for keeping track of what data has been processed
            safe_mkdir("save_data")
            self.index_book = {}
            for i, path in enumerate(filter(valid_audio_file, os.listdir(self.read_path))):
                self.index_book[i] = [path, False] # Path and status (i.e. has it been labelled yet)
        
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
        """
        Saves result dataset, as well as (in specific case of WavFolderPipeline) an index book of which audio files have been 
        looked at so far
        """
        super().save_dataset()
        joblib.dump(self.index_book, "save_data/index_book.joblib")

    @abstractmethod
    def fetch(self) -> BatchElement:
        """
        Fetch a batch element from data source. Should call id_pop to get path in most cases.
        """
        pass

    def id_pop(self) -> Dict[str, Any]:
        """
        Pop an id and path from the index_book queue. Returns a dict that can be given directly to a batch element constructor
        as keyword arguments.
        """
        id = self.id_queue.pop(0)
        path, _ = self.index_book[id]
        path = os.path.join(self.read_path, path)

        return {"id" : id, "path" : path}

    @abstractmethod
    def post(self, batch_element : BatchElement):
        """
        Post completed batch element to data destination. Should call id_complete() before returning in most cases.
        """
        pass

    def id_complete(self, id : int, row : Dict[str, Any]):
        """
        Given a row to add to dataset, marks corresponding entry in index_book complete
        """
        path, _ = self.index_book[id]
        self.add_row_to_dataset(row)

        self.index_book[id][1] = True
        self.save_dataset()

