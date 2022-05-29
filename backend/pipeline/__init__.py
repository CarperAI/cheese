from abc import abstractmethod
from typing import List

from pyparsing import ParseExpression
from backend.orchestrator  import Orchestrator
from backend.data import BatchElement
from backend.tasks import Task

class Pipeline:
    """Abstract base class for a data pipeline. Processes data and communicates with orchestrator"""

    @abstractmethod
    def orchestrator_preprocess(self, batch_element: BatchElement) -> Task:
        """Preprocesses batch element before it is passed to orchestrator"""
        pass

    @abstractmethod
    def orchestrator_postprocess(self, batch_element: BatchElement) -> BatchElement:
        """Postprocesses batch element after it is received from orchestrator"""
        pass

    @abstractmethod
    def create_data_task(self) -> Task:
        """Creates a task for the orchestrator"""
        pass

    @abstractmethod
    def receive_data_task(self, task: Task):
        """Receives a single task from the orchestrator"""
        pass

    @abstractmethod
    def receive_data_tasks(self, tasks: List[Task]):
        """Receives a list of tasks from the orchestrator"""
        pass