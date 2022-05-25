
from dataclasses import dataclass
from typing import List, Tuple

from datasets import load_dataset, Dataset
import pandas as pd


from backend.data import *

@dataclass
class TextCaptionBatchElement(BatchElement):
    id : int
    text : str # Text we want captioner to see
    captions : List[Tuple[Tuple[int, int], str]] # List of tuples of (start, end) indices and captions

class TextCaptionPipeline(Pipeline):
    """
    Pipeline for captioning dataset of text
    """

    def __init__(self, read_path, write_path):
        super().__init__()

        self.read_path = read_path
        self.write_path = write_path

        # Source dataset
        self.dataset = load_dataset(read_path) # should have column ['text']
        self.total_items = len(self.dataset["text"])
        self.done = False

        # Captioned dataset
        try:
            self.res_dataset = load_dataset(write_path)
            self.finished_items = len(self.res_dataset["text"])
        except:
            # intialize empty dataset as pandas df, then convert to dataset
            self.res_dataset = pd.DataFrame(columns=['id', 'text', 'captions'])
            self.res_dataset = Dataset.from_pandas(self.res_dataset)
            self.res_dataset.save_to_disk(write_path)
            self.finished_items = 0

        self.current_index = self.finished_items


    def orchestrator_preprocess(self, orch_in: BatchElement) -> BatchElement:
        return orch_in
    
    def orchestrator_postprocess(self, orch_out: BatchElement) -> BatchElement:
        return orch_out

    def send_to_orchestrator(self) -> BatchElement:
        """
        Get dataset item and send it to orchestrator
        """

        text = self.dataset["text"][self.current_index]
        batch_element = TextCaptionBatchElement(self.current_index, text, [])
        batch_element = self.orchestrator_preprocess(batch_element)

        self.current_index += 1
        return batch_element
    
    def receive_from_orchestrator(self, orch_out: BatchElement):
        """
        Receive batch element from orchestrator
        """

        batch_element = self.orchestrator_postprocess(orch_out)
        new_item = {'id': batch_element.id, 'text': batch_element.text, 'captions': batch_element.captions}
        self.res_dataset.add_item(new_item)

        self.res_dataset.save_to_disk(self.write_path)
        self.finished_items += 1
        done = self.finished_items == self.total_items
    


        

    
