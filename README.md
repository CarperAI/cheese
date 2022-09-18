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
As an example, the following script runs an image selection task, where two images from LAION-art dataset are presented and the labeller is asked to choose one.
```
python -m examples.image_selection
```

# Custom tasks in Gradio
Refer to examples/image_selection.py for a comprehensive example on how to create your own custom task with a Gradio UI.
