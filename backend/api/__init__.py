from typing import ClassVar

class CHEESEAPI:
    def __init__(self, pipeline_cls, orch_cls, client_cls = None, model_cls = None, pipeline_kwargs = {}, orch_kwargs = {}):
        self.pipeline = pipeline_cls(**pipeline_kwargs)
        self.orch = orch_cls(**orch_kwargs)
        self.client_cls = client_cls
        self.model_cls = model_cls
