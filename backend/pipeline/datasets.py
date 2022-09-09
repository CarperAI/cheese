from abc import abstractmethod
from typing import Iterable, Dict, Any

from datasets import Dataset

from backend.pipeline import Pipeline
from backend.utils import make_empty_dataset

class DatasetPipeline(Pipeline):
    """
    Base class for any pipeline that writes results to a datasets.Dataset object
    """
    def __init__(self):
        super().__init__()

        self.write_path : str = None
        self.res_dataset : Dataset = None

    def save_dataset(self):
        if self.res_dataset is None:
            raise Exception("Error: Attempted to save result dataset without every initializing it.")
        if self.write_path is None:
            raise Exception("Error: Attempted to save result dataset without every specifiying a path to write to")

        self.res_dataset.save_to_disk(self.write_path)
    
    def init_dataset_from_col_names(self, col_names : Iterable[str]) -> Dataset:
        """
        Initialize a dataset from column names.

        :param col_names: List of names for columns of dataset
        :type col_names: Iterable[str]
        """
        return make_empty_dataset(col_names)
    
    @abstractmethod
    def init_dataset(self) -> Dataset:
        """
        Create initial dataset to write batch elements to after they have been labelled/evaluated. Derived class
        can easily implement with init_dataset_from_col_names(...)

        :return: Empty dataset object
        :rtype: datasets.Dataset
        """
        pass

    def add_row_to_dataset(self, row : Dict[str, Any]):
        """
        Add single row to result dataset
        """
        self.res_dataset = self.res_dataset.add_item(row)

