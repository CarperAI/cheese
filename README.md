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
python test_api.py
```
