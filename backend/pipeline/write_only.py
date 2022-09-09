from abc import abstractmethod

import os
from datasets import load_from_disk, Dataset

import numpy as np

from backend.pipeline.datasets import DatasetPipeline
from backend.data import BatchElement

class WriteOnlyPipeline(DatasetPipeline):
    """
    Base pipeline for any task that involves giving users empty data but writing concrete results
    (i.e. prompting model generation, then receiving feedback)
    """
    def __init__(self, write_path : str, force_new : bool = False):
        super().__init__()

        self.write_path = write_path

        try:
            assert not force_new
            self.res_dataset = load_from_disk(write_path)
        except:
            self.res_dataset = self.init_dataset()

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

    @abstractmethod
    def fetch(self) -> BatchElement:
        """
        Generate empty BatchElement to send to client
        """
        pass
    
    @abstractmethod
    def post(self, batch_element : BatchElement):
        """
        Post completed batch element to data destination.
        """
        pass
    
