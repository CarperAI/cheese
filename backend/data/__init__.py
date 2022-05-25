
from abc import abstractmethod
from typing import Callable, Dict, Iterable, Tuple

class BatchElement:
    """Abstract base class for BatchElements. Store all kinds of data being passed around CHEESE"""
    pass


class Pipeline:
    """Abstract base class for a data pipeline. Processes data and communicates with orchestrator"""

    @abstractmethod
    def orchestrator_preprocess(self, batch_element: BatchElement) -> BatchElement:
        """Preprocesses batch element before it is passed to orchestrator"""
        pass

    @abstractmethod
    def orchestrator_postprocess(self, batch_element: BatchElement) -> BatchElement:
        """Postprocesses batch element after it is received from orchestrator"""
        pass