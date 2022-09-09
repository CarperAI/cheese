from dataclasses import dataclass

from backend.data import BatchElement
import numpy as np

@dataclass
class AudioRatingBatchElement(BatchElement):
    id : int = None
    path : str = None
    rating : int = -1
    comment : str = ""
