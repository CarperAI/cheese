
from dataclasses import dataclass
from typing import List, Tuple

from backend.data import BatchElement

@dataclass
class TextCaptionBatchElement(BatchElement):
    id : int
    text : str # Text we want captioner to see
    caption_index : List[Tuple[int, int]] # List of tuples of (start, end) indice
    captions : List[str]


    


        

    
