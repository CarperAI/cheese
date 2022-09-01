# Coadaptive Harness for Effective Evaluation, Steering, & Enhancement
Used for adaptive human in the loop evaluation of language and embedding models.

# Getting Started
You need rabbitmq for the messaging system in the backend. It can be installed easily with conda as follows:
```
conda install -c conda-forge rabbitmq-server
```
Then start the server (should do this on a different screen/window)
```
rabbitmq-server
```
Assuming a source dataset is present (you may generate one with the generate_test_dataset.py script), the following command will run a text captioning task on the source dataset, returning a URL for you to access the labelling UI:
```
python -m examples.test_gradio_api
```

# Custom tasks in Gradio
Making new tasks with a gradio frontend in CHEESE is very simple! You will have to define subclasses for:
backend.data.BatchElement (a dataclass)
backend.pipeline.Pipeline
backend.client.gradio_client.GradioClient
backend.client.gradio_client.GradioClientFront

You may refer to audio_rating.py scripts within the folders for the above objects for an example on how to use CHEESE for the task of rating a folder of WAV files. The script relevant to running the task is examples/audio_test.py
