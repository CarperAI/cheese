from typing import ClassVar

class CHEESEAPI:
    def __init__(self, pipeline_cls, orch_cls, client_cls = None, model_cls = None, pipeline_kwargs = {}, orch_kwargs = {}):
        self.pipeline = pipeline_cls(**pipeline_kwargs)
        self.orch = orch_cls(**orch_kwargs)
        self.client_cls = client_cls
        self.model_cls = model_cls

    def create_client(self, id : int, **kwargs):
        """
        Create a client instance with given id and any other optional parameters.
        
        :param id: A unique identifying number for the client.
        :type id: int

        :param kwargs: Any other parameters to be passed to the client constructor.
        """
        if self.client_cls is None:
            raise Exception("No client class specified")

        new_client = self.client_cls(id, **kwargs)
        self.orch.set_client(new_client)
    
    def create_model(self, **kwargs):
        """
        Create instance of model for labelling assistance

        :param kwargs: Any parameters to be passed to the model constructor.
        """
        raise NotImplementedError

    def step(self) -> bool:
        """
        Gets tasks back from clients, sends finished tasks back to pipeline, handles queued tasks, receives new ones if available.
        Returns True once pipeline is exhausted and task queues are all empty.
        """

        # Order of priority:
        # 1. Getting tasks back from BUSY clients or model
        # 2. Sending finished tasks to pipeline
        # 3. Handling tasks in queue
        # 4. Receiving new tasks from pipeline

        # Always prioritize getting tasks from clients done first
        for client in self.orch.clients:
            client.handle_task() 
            
        # Have orch receive tasks from any finished clients
        self.orch.query_clients()

        # Get completed tasks and send them to pipeline
        self.pipeline.receive_data_tasks(self.orch.get_completed_tasks())
        
        # Handle tasks in queue
        self.orch.handle_task()

        # If orch has room for more tasks, take some from pipeline
        exhausted_pipe = False
        if self.orch.is_free():
            # Get 
            task = self.pipeline.create_data_task()
            if task is not None: 
                self.orch.receive_task(task)
            else:
                exhausted_pipe = True

        if exhausted_pipe and self.orch.get_total_tasks() == 0:
            return True

        return False

    def backup_orch_state(self):
        """
        Backup orchestrator state
        """
        self.orch.backup_state()

    

