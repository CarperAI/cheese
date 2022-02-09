from __future__ import annotations

from dataclasses import dataclass
from abc import abstractmethod

import sys
from typing import Dict, Tuple, Iterable, List, Any
from typeguard import typechecked

_ORCHESTRATORS: Dict[str, any] = {}  # registry


def register_orchestrator(name):
    """Decorator used register a CHEESE architecture
        Args:
            name: Name of the architecture
    """

    def register_class(cls, name):
        _ORCHESTRATORS[name] = cls
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
class PipelineConfig:
    #Pipeline configs

@register_orchestrator
class BaseOrchestrator:

    #def __init__(self):

    @abstractmethod
    def get_data(self,data: BaseDataPipeline):
        '''calls datapipeline for data, returns iterable[DataPipelineOutput]'''