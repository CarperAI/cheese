from abc import ABC, abstractmethod

class BaseGlobalOrchestrator:
    
class BaseTaskPipeline:

class BaseSurveyPipeline:

class BaseDataPipeline(Dataset):
    ''' DataPipeline wrapper class to access story datasets'''
    def __init__(
        self,
        path: str = "dataset",
    ):
        dataset = load_from_disk(path)
        story = dataset['story']
        evaluation = dataset['evaluation']

    def __getstory__(self, index: int) -> ITT[str]:
        ''' returns story from database'''
        return self.story[index]

    def __geteval__ (self, index:int) -> ITT[str]:
        ''' returns current eval for some story'''
        return self.evaluation[index]
        

class BaseInferencePipeline:

    def __MakeStoryClozeElement__(self, mode, task):
        return pipeline(mode, task)
        
