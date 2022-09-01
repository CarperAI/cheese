from abc import abstractmethod
from typing import Dict, Any, Iterable

import webdataset as wds
from datasets import load_from_disk, Dataset
import pandas as pd
import joblib
import numpy as np

from backend.pipeline.datasets import DatasetPipeline
from backend.data import BatchElement
from backend.utils import safe_mkdir, make_empty_dataset

class IterablePipeline(DatasetPipeline):
    """
    Base class for any pipeline reading from an iterable dataset
    Writes results to Datasets dataset

    :param iter: The iterable to be used to read data from
    :type iter: Iterable

    :param write_path: Path to write result dataset to
    :type write_path: str

    :param force_new: Whether to force a new dataset (as opposed to recovering saved progress from write_path)
    :type force_new: bool

    :param max_length: Maximum number of entries to produce for output dataset. Defaults to infinity.
    """
    def __init__(self, iter : Iterable, write_path : str, force_new : bool = False, max_length = np.inf):
        super().__init__()

        self.data_source = iter

        self.fail_next = False # Made true once next(self.data_source) fails

        self.write_path = write_path
        self.max_length = max_length

        try:
            assert not force_new
            self.res_dataset = load_from_disk(write_path)
            self.progress = joblib.load("save_data/progress.joblib")
        except:
            self.res_dataset = self.init_dataset()

            safe_mkdir("save_data")
            self.progress = 0
            self.save_dataset()
    
    @abstractmethod
    def init_dataset(self) -> Dataset:
        """
        Create initial dataset to write batch elements to after they have been labelled/evaluated. Derived class
        can easily implement with init_dataset_from_col_names(...)

        :return: Empty dataset object
        :rtype: datasets.Dataset
        """
        pass

    def exhausted(self) -> bool:
        return self.progress >= self.max_length or self.fail_next

    def save_dataset(self):
        """
        Save dataset and progress.
        """
        super().save_dataset()
        joblib.dump(self.progress, "save_data/progress.joblib")

    def preprocess(self, x : Any) -> Any:
        """
        When data source is iterated over, this function is applied to all outputted data.
        Should also validate data and raise InvalidDataException if data invalid.
        """
        return x

    @abstractmethod
    def fetch(self) -> BatchElement:
        """
        Fetch a batch element from data source. Should call fetch_next() in most cases.
        """
        pass

    def fetch_next(self) -> Any:
        """
        Attempts to get next item from webdataset. Returns None if there is no such item.
        """
        try:
            while True:
                res = next(self.data_source)
                try:
                    return self.preprocess(res)
                except Exception as e:
                    if type(e) is InvalidDataException:
                        continue
                    else:
                        raise e
            
        except Exception as e:
            if type(e) is StopIteration:
                self.fail_next = True
                return None
            else:
                raise e

    @abstractmethod
    def post(self, batch_element : BatchElement):
        """
        Post completed batch element to data destination. Should call post_row() before returning in most cases.
        """
        pass

    def post_row(self, row : Dict[str, Any]):
        """
        Given a row to add to result dataset: updates progress, adds row and saves.
        """
        self.res_dataset = self.res_dataset.add_item(row)
        self.progress += 1
        self.save_dataset()

class InvalidDataException(Exception):
    pass


        



