from typing import Iterable
from Data import DataPipelineOutput
from Inference import BaseInferenceOutput

from dataclasses import dataclass

_SURVEYPIPELINE = Dict[str,any] = {}

def register_surveypipeline(name):
    """Decorator used register a survey pipeline

        Args:
            name: Name of the architecture
    """

    def register_class(cls, name):
        _SURVEYPIPELINE[name] = cls
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
class BaseSurveyPipelineConfig:
    name : str = "BaseSurveyPipelineConfig"

@dataclass
class BaseSurveyInput:
    data_output : Iterable[DataPipelineOutput]
    inference_output : Iterable[BaseInferenceOutput]

@dataclass
class BaseSurveyOutput:
    HTML : str

@typechecked
class BaseSurveyPipeline:
    def __init__(self, config: BaseSurveyPipelineConfig):
        self.config = config

    def create_htmlfile(self, input: BaseSurveyInput) -> BaseSurveyOutput:
        raise Exception ("Must be overridden in child class")

    def create_report(self):
        # create output from completion of task
        return None


def get_surveylines(name : str) -> BaseSurveyPipeline:
    """
    :param name:
        Name refers to the name of corresponding survey pipeline
    :return:
        A survey pipeline from the decorator registry
    """
    return _SURVEYPIPELINE[name.lower()]

def get_surveypipelines_names() -> List[str]:
    """
    Gets the list of surveypipeline names
    :return:
        A list of survey pipeline names
    """
    return _SURVEYPIPELINE.keys()


