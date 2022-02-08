from __future__ import annotations

from dataclasses import dataclass
from abc import abstractmethod

import sys
from typing import Dict, Tuple, Iterable, List
from typeguard import typechecked

_BASEINFERENCEPIPELINE = Dict[str,any] = {}
def reigster_BaseInferencePipeline(name):
    """Decorator used register a base inference pipeline

        Args:
            name: Name of the architecture
    """

    def register_class(cls, name):
        _BASEINFERENCEPIPELINE[name] = cls
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
class InferencePipelineConfig:
    name: str = "BaseInferenceName"
    task: str = "BaseInferenceTask"

@dataclass
class InferencePipelineOutput:
    output_string : str = ""

class BaseInferencePipeline:
    def __init__(self, config: InferencePipelineConfig):
        self.config = config

    def process(self) -> Interable[InferencePipelineOutput]:
        '''
        Args:
            Text
        :return:
            A StoryCloze of Text
        '''
        raise Exception("Error: Must be overriden in child class.")


def get_inferencepipelines(name : str) -> BaseDataPipeline:
    """
    :param name:
        Name refers to the name of corresponding inference pipeline
    :return:
        An inference pipeline from the decorator registry
    """
    return _BASEINFERENCEPIPELINE[name.lower()]

def get_inferencepipelines_names() -> List[str]:
    """
    Gets the list of inference pipeline names
    :return:
        A list of inference pipeline names
    """
    return _BASEINFERENCEPIPELINE.keys()

