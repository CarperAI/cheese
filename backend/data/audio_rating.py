from dataclasses import dataclass

from backend.data import BatchElement
import numpy as np

@dataclass
class AudioRatingBatchElement(BatchElement):
    id : int
    audio : np.ndarray # [channels, samples]
    sr : int # sampling rate
    rating : int = -1
    comment : str = ""