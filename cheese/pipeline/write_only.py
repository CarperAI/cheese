from abc import abstractmethod

import os
from datasets import load_from_disk, Dataset

import numpy as np

from cheese.pipeline.datasets import DatasetPipeline
from cheese.data import BatchElement

class WriteOnlyPipeline(DatasetPipeline):
    """
    Base pipeline for any task that involves giving users empty data but writing concrete results
    (i.e. prompting model generation, then receiving feedback)

    :param write_path: The path to write the result dataset to
    :type write_path: str

    :param force_new: Whether to force a new dataset to be created, even if one already exists at the write path
    :type force_new: bool
    """
    def __init__(self, write_path : str, force_new : bool = False, **kwargs):
        super().__init__(**kwargs)

        self.write_path = write_path
        self.force_new = force_new

        try:
            assert not force_new
            assert self.load_dataset()
            print(f"Succesfully loaded dataset with {len(self.res_dataset)} entries.")
        except:
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
    
