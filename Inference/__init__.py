from __future__ import annotations

from dataclasses import dataclass
from abc import abstractmethod

import sys
from typing import Dict, Tuple, Iterable, List, Any
from typeguard import typechecked

from Data import DataPipelineOutput

_INFERENCEPIPELINE = Dict[str, any] = {}


def reigster_inferencepipeline(name):
    """Decorator used register an inference pipeline

        Args:
            name: Name of the architecture
    """

    def register_class(cls, name):
        _INFERENCEPIPELINE[name] = cls
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
    name: str = "InferencePipelineName"
    task: str = "InferencePipelineTask"


@dataclass
class InferencePipelineInput:
    data_output_: Iterable[DataPipelineOutput]


@dataclass
class InferencePipelineOutput:
    output_string: str = ""


@typechecked
class BaseInferencePipeline:
    def __init__(self, config: InferencePipelineConfig):
        self.config = config

    @abstractmethod
    def process(self, data: DataPipelineOutput,*args) -> Iterable[InferencePipelineOutput]:
        """Takes
        Args:
            DataPipelineOutput
            Model Args
        Returns:
            Iterable[InferencePipelineOutput]
            """
        raise Exception("Must be overridden in child class")


def get_inferencepipelines(name: str) -> BaseInferencePipeline:
    """
    :param name:
        Name refers to the name of corresponding inference pipeline
    :return:
        An inference pipeline from the decorator registry
    """
    return _INFERENCEPIPELINE[name.lower()]


def get_inferencepipelines_names() -> _dict_keys[Any, Any]:
    """
    Gets the list of inference pipeline names
    :return:
        A list of inference pipeline names
    """
    return _INFERENCEPIPELINE.keys()
