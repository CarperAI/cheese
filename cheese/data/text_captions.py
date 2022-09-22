
from dataclasses import dataclass
from typing import List, Tuple

from cheese.data import BatchElement

@dataclass
class TextCaptionBatchElement(BatchElement):
    id : int = None
    text : str = None # Text we want captioner to see
    caption_index : List[Tuple[int, int]] = None # List of tuples of (start, end) indice
    captions : List[str] = None


    


        

    
