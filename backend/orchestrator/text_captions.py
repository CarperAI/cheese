from dataclasses import dataclass

from backend.tasks import Task
from backend.tasks import TaskType as TT
from backend.orchestrator import Orchestrator

class TextCaptionOrchestrator(Orchestrator):
    """
    Orchestrator for text captions.
    """

    def __init__(self):
        super().__init__()

    def receive_task(self, task: Task):
        """
        Receives a task from arbitrary source.
        """
        self.tasks.append(task)

    def handle_task(self) -> bool:
        """
        Handles the top task in the queue. Signals whether it was successful or not
        """

        # Prioritize active tasks
        if len(self.active_tasks) == 0:
            if len(self.tasks) == 0:
                return False # No tasks to do
            task = self.tasks.pop(0)
        else:
            task  = self.active_tasks.pop(0)

        success = False
        
        if task.receiver == TT.PIPELINE:
            # If pipeline is receiving task, that means the task is done
            self.done_tasks.append(task)
            success = True
        elif task.receiver == TT.USER:
            # Find a free client and assign task to it
            for client in self.clients:
                if client.is_free():
                    task.client_id = client.id
                    client.receive_task(task)
                    success = True
                    break
        elif task.receiver == TT.MODEL:
            raise NotImplementedError("Model receiving task not implemented yet.")
        
        if not success:
            # If task was not handled, put it back at first place in queue
            self.tasks.insert(0, task)
        
        return success
    
    def query_clients(self) -> bool:
        """
        Query the clients for completed tasks, returns whether any tasks were completed.
        """
        success = False
        for client in self.clients:
            task = client.get_done_task()
            if task is not None:
                self.active_tasks.append(task)
                success = True
        
        return success

        


