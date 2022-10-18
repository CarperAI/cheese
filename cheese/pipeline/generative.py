from abc import abstractmethod
from typing import Iterable, Dict, Any

from cheese.pipeline.write_only import WriteOnlyPipeline
from cheese.data import BatchElement

import threading
import joblib

class GenerativePipeline(WriteOnlyPipeline):
    """
    Base pipeline for any task that requires creating model generations and
    displaying them to users efficiently. Fills up a buffer with generations continuously,
    then serves them to users as they request them.

    :param iterator: If model needs prompts or some predefined input data,
    it should be provided by some iterator. Iterator should create some sort of dictionary
    :type iterator: Iterable[Dict]

    :param batch_size: The number of generations to produce in a single step
    :type batch_size: int

    :param buffer_size: The number of generations to keep in the buffer
    :type buffer_size: int

    :param log_progress: Whether to log progress through iterator into a file
    :param write_path: The path to write the result dataset to
    :type write_path: str

    :param force_new: Whether to force a new dataset to be created, even if one already exists at the write path
    :type force_new: bool
    """
    def  __init__(self, iterator : Iterable[Dict], batch_size : int = 1, buffer_size : int = 32, log_progress : bool = True, max_length : int = None, **kwargs):
        super().__init__(**kwargs)

        self.iterator = iterator
        self.iterator_exhausted = False

        self.batch_size = batch_size
        self.buffer_size = buffer_size

        self.buffer = []
        self.buffer_ready = False # Becomes true when buffer gets intial item

        self.progress = 0
        self.log_progress = log_progress
        self.max_length = max_length
    
        if self.log_progress and not self.force_new:
            # If we're logging progress, try to load progress and update iterator to reflect it
            try:
                self.progress = joblib.load("save_data/progress.joblib")
                for _ in range(self.progress): next(self.iterator)
            except Exception as e:
                print("Error loading progress:", e.with_traceback())
                pass
    
    def init_buffer(self):
        """
        Start filling buffer. Must call this in subclass, ideally at end of init
        """
        self.buffer_thread = threading.Thread(target=self.populate_buffer)
        self.buffer_thread.start()

    @abstractmethod
    def generate(self, model_input : Iterable[Dict]) -> Iterable[BatchElement]:
        """
        Generate a batch of generations from input data. It is assumed
        the input is a batch.
        """
        pass

    @abstractmethod
    def extract_data(self, batch_element : BatchElement) -> Dict:
        """
        Extract data from batch element to be saved to dataset. Use
        this to convert BatchElement to a dictionary.
        """
        pass

    def get_stats(self):
        return {
            "progress" : self.progress,
            "buffer_content" : self.buffer_content(),
            "ready" : self.buffer_ready
        }

    def exhausted(self) -> bool:
        """
        Is there any more data to read?
        """
        if self.iterator_exhausted or self.progress >= self.max_length:
            return True
        return False
    
    def save_dataset(self):
        super().save_dataset()
        if self.log_progress:
            joblib.dump(self.progress, "save_data/progress.joblib")

    def buffer_content(self) -> int:
        """
        How many generations are in the buffer?
        """
        return len(self.buffer)

    def populate_buffer(self):
        """
        Fill up the buffer with new generations
        """
        while len(self.buffer) < self.buffer_size and not self.exhausted():
            try:
                model_input = [next(self.iterator) for _ in range(self.batch_size)]
                new_elems : Iterable[BatchElement] = self.generate(model_input)
                self.buffer += new_elems
                self.buffer_ready = True
                print("hi 2")
            except StopIteration:
                self.iterator_exhausted = True
                break

    def fetch(self) -> BatchElement:
        if len(self.buffer) == 0:
            raise Exception("Error: Tried to fetch data before any was created. Please wait longer for buffer to fill or increase its capacity.")
        elem = self.buffer.pop(0)
        return elem
    
    def post(self, be : BatchElement):
        self.progress += 1

        if not be.error:
            row = self.extract_data(be)
            self.add_row_to_dataset(row)
