from __future__ import annotations

import dataclasses
from abc import abstractmethod

import sys
from typing import Dict, Tuple, Iterable, List
from typeguard import typechecked


_DATAPIPELINES: Dict[str, any] = {}


def register_datapipeline(name):
    """Decorator used register a data pipeline

        Args:
            name: Name of the architecture
    """

    def register_class(cls, name):
        _DATAPIPELINES[name] = cls
        setattr(sys.modules[__name__], name, cls)
        return cls

    if isinstance(name, str):
        name = name.lower()
        return lambda c: register_class(c, name)

    cls = name
    name = cls.__name__
    register_class(cls, name.lower())

    return cls

@dataclass
class BaseDataPipelineConfig:
    name : str = "BaseDataPipelineConfig"
    n_examples : int = -1 # defaults to all examples

@dataclass
class DataPipelineOutput:
    examples : Iterable[str]

@typechecked
class BaseDataPipeline:
    def __init__(self, config : BaseDataPipelineConfig):
        self.config = config

    def ingest(self):
        """
        Args:
            None
        :return:
            Returns raw unprocessed output for BaseDataPipeline.process
        """
        raise Exception("Error: Must be overridden in child class.")

    def process(self) -> Iterable[DataPipelineOutput]:
        """
        Args:
            None (for now)
        :return:
            An iterable of data pipeline outputs
        """
        raise Exception("Error: Must be overridden in child class.")


from Data.shmoops import *

def get_datapipelines(name : str) -> BaseDataPipeline:
    """
    :param name:
        Name refers to the name of corresponding data pipeline
    :return:
        A data pipeline from the decorator registry
    """
    return _DATAPIPELINES[name.lower()]

def get_datapipelines_names() -> List[str]:
    """
    Gets the list of datapipeline names
    :return:
        A list of data pipeline names
    """
    return _DATAPIPELINES.keys()


my_data_pipeline = get_datapipelines("ShmoopsDataPipeline")
