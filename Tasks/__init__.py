from __future__ import annotations

import dataclasses
from abc import abstractmethod

import sys
from typing import Dict, Tuple, Iterable, List

from typeguard import typechecked

from Data import DataPipelineOutput

_TASKPIPELINE: Dict[str,any] = {}

def register_taskpipeline(name):
    """Decorator used register a task pipeline

        Args:
            name: Name of the architecture
    """

    def register_class(cls, name):
        _TASKPIPELINE[name] = cls
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
class BaseTaskPipelineConfig:
    name: str = "BaseTaskPipelineConfig"
    #...


@typechecked
class BaseTaskPipeline:
    def __init__(self, config:BaseTaskPipelineConfig):
        self.config = config

    def construct_task(self) -> BaseSurveyInput:
        # call data pipeline
        # constructs prompts as needed
        # feed output the data+prompts to inference pipeline
        # returns BaseSurveyInput
        raise Exception("Must be overriden in child class.")

    def construct_survery(self, survey_input : BaseSurveyInput) -> BaseSurveyOutput:
        # calls construct task
        # Calls survey pipeline using the output from construct task
        # returns the finalized survey, saves survey piepline output to css/html, and stores survey in memory
        raise Exception("Must be overridden in child class.")

    def upload_prolific(self):
        #uploads


def get_taskpipelines(name : str) -> BaseTaskPipeline:
    """
    :param name:
        Name refers to the name of corresponding task pipeline
    :return:
        A task pipeline from the decorator registry
    """
    return _TASKPIPELINE[name.lower()]

def get_taskpipelines_names() -> List[str]:
    """
    Gets the list of taskpipeline names
    :return:
        A list of task pipeline names
    """
    return _TASKPIPELINE.keys()



