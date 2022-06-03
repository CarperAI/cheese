from backend.pipeline.text_captions import TextCaptionPipeline
from backend.orchestrator.text_captions import TextCaptionOrchestrator
from backend.client.sim_client import SimClient

from datasets import load_from_disk

if __name__ == "__main__":
    pipe = TextCaptionPipeline("dataset", "data_res", force_new = True)
    orch = TextCaptionOrchestrator()
    client = SimClient()

    orch.set_client(client)

    # Generate some tasks from the pipeline (3)
    tasks = [pipe.create_data_task() for _ in range(3)]

    # Send tasks to orchestrator and handle 1
    orch.receive_tasks(tasks)
    res1 = orch.handle_task()
    res2 = orch.handle_task()

    assert res1
    assert not res2

    print(client.task.data.text)

    client.handle_task()
    
    print(client.task.data.captions)   

    res1 = orch.query_clients()
    res2 = orch.query_clients()

    assert len(orch.tasks) == 2
    assert len(orch.active_tasks) == 1

    assert res1
    assert not res2

    orch.handle_task()

    # Make sure orchestrator only handled the active task
    assert client.is_free()

    # Should have finished task now
    assert len(orch.done_tasks) == 1

    pipe.receive_data_tasks(orch.get_completed_tasks())
    pipe.save_dataset()

    # Test to make sure this showed up in the final dataset
    res_dataset = load_from_disk("data_res")
    print(res_dataset["text"])
    print(res_dataset["captions"])
    print(res_dataset["caption_index"])
    print(res_dataset["id"])











