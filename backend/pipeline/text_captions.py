import pandas as pd
from datasets import load_from_disk, Dataset
import pickle

from typing import List

from backend.pipeline import Pipeline
from backend.data import BatchElement
from backend.data.text_captions import TextCaptionBatchElement
from backend.tasks import Task

class TextCaptionPipeline(Pipeline):
    """
    Pipeline for captioning dataset of text
    """

    def __init__(self, read_path : str, write_path : str, force_new : bool = False):
        super().__init__()

        self.read_path = read_path
        self.write_path = write_path

        # Source dataset
        self.dataset = load_from_disk(read_path) # should have column ['text']
        self.total_items = len(self.dataset["text"])
        self.done = False # Have we finished creating new dataset?

        # Captioned dataset
        try:
            assert not force_new
            self.res_dataset = load_from_disk(write_path)
            self.finished_items = len(self.res_dataset["text"])
        except:
            # intialize empty dataset as pandas df, then convert to dataset
            self.res_dataset = pd.DataFrame(columns=['id', 'text', 'caption_index', 'captions'])
            self.res_dataset = Dataset.from_pandas(self.res_dataset)
            self.res_dataset.save_to_disk(write_path)
            self.finished_items = 0

        self.current_index = self.finished_items

    def queue_task(self) -> bool:
        """
        Creates a task and queue to text captioning client.
        
        :return: True if succesful, False if pipeline exhausted.
        :rtype: bool
        """

        if self.done or self.current_index == self.total_items:
            return False

        text = self.dataset["text"][self.current_index]
        batch_element = TextCaptionBatchElement(self.current_index, text, [], [])

        task = Task(batch_element)
        tasks = pickle.dumps(task)

        self.publisher.publish(
            routing_key = 'client',
            payload = tasks
        )

        #self.msg_channel.basic_publish(
        #    exchange = '',
        #    routing_key = 'client',
        #    body = tasks
        #)

        self.current_index += 1
        return True
    
    def dequeue_task(self, tasks : str):
        """
        Receive message corresponding to task.

        :param tasks: Task serialized as string.
        :type tasks: str
        """
        
        task = pickle.load(tasks)
        batch_element = task.data

        caption_index = [elem for elem in batch_element.caption_index]
        captions = [elem for elem in batch_element.captions]

        new_item = {'id': batch_element.id, 'text': batch_element.text,
         'caption_index' : caption_index, 'captions': captions}
        self.res_dataset = self.res_dataset.add_item(new_item)
        self.save_dataset()

        self.finished_items += 1
        self.done = self.finished_items == self.total_items
    
    def save_dataset(self):
        self.res_dataset.save_to_disk(self.write_path)