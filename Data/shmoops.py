from Data import BaseDataPipeline, BaseDataPipelineConfig, DataPipelineOutput, register_datapipeline
from typing import List, Tuple, Iterable

@dataclass
class ShmoopsDataPipelineConfig(BaseDataPipelineConfig):
    shmoop_specific_string : str

@dataclasses
class ShmoopsDataPipelineOutput(DataPipelineOutput):
    shmoop_specific_string : str


# in this example task, we have a set of stories and gold standard summaries.
# we ask a language model to summarize the story, and we present the generated summary pairwise with the gold
# standard summary. We ask participants to determine based off of a number of attributes which summary is better

# For example:
# 1. Which summary is more coherent?
# 2. Which summary is more grammatically correct?
# 3. Which summary is more accurate to the text?
@register_datapipeline
class ShmoopsDataPipeline(BaseDataPipeline):
    def __init__(self, config : ShmoopsDataPipelineConfig):
        super().__init__(config)

    def ingest(self) -> List[Tuple[str, str]]:
        # load shmoops from text
        # TODO: Fix!!
        return None

    def process(self) -> Iterable[DataPipelineOutput]:
        # reads the data from a corresponding database or file
        data = self.ingest()

        # do some processing
        # beep boop

        # get the data pipeline output
        data_output = None
        return data_output
