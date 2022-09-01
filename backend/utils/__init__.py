from typing import Iterable
from datasets import Dataset

import pandas as pd
import os

def safe_mkdir(path : str):
    """
    Make directory if it doesn't exist, otherwise do nothing
    """
    if os.path.isdir(path):
        return
    os.mkdir(path)

def make_empty_dataset(colNames : Iterable[str]) -> Dataset:
    res = pd.DataFrame(columns = colNames)
    return Dataset.from_pandas(res)
