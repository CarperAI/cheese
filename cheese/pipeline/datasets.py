from abc import abstractmethod
from typing import Iterable, Dict, Any

from datasets import Dataset

from cheese.pipeline import Pipeline

class DatasetPipeline(Pipeline):
    """
    Base class for any pipeline thats data destination is a datasets.Dataset object
    
    :param format: Format to save result dataset to. Defaults to arrow. Can be arrow or csv.
    :type format: str

    :param save_every: Save dataset whenever this number of rows is added.
    :type save_every: int
    """
    def __init__(self, format : str = "csv", save_every  : int = 1):
        super().__init__()

        self.write_path : str = None
        self.res_dataset : Dataset = None
        self.format = format
        
        self.save_every = save_every
        self.save_accum = 0

    def save_dataset(self):
        """
        Saves the result dataset to the write path (assuming it has been specified by subclass).
        Does nothing if there is no data to save yet.
        """
        if self.res_dataset is None:
            return
        if self.write_path is None:
            raise Exception("Error: Attempted to save result dataset without every specifiying a path to write to")

        if self.format == "arrow":
            self.res_dataset.save_to_disk(self.write_path)
        elif self.format == "csv":
            self.res_dataset.to_csv(self.write_path)

    def add_row_to_dataset(self, row : Dict[str, Any]):
        """
        Add single row to result dataset and then saves.

        :param row: The row, as a dictionary, to add to the result dataset
        :type row: Dict[str, Any]
        """
        if self.res_dataset is None:
            row = {key : [row[key]] for key in row}
            self.res_dataset = Dataset.from_dict(row)
        else:
            self.res_dataset = self.res_dataset.add_item(row)

        self.save_accum += 1
        if self.save_accum >= self.save_every:
            self.save_dataset()
            self.save_accum = 0

