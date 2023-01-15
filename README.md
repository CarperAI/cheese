[![DOI](https://zenodo.org/badge/453764663.svg)](https://zenodo.org/badge/latestdoi/453764663)

[docs-image]: https://readthedocs.org/projects/cheese1/badge/?version=latest
[docs-url]: https://cheese1.readthedocs.io/en/latest/?badge=latest

# Coadaptive Harness for Effective Evaluation, Steering, & Enhancement
Used for adaptive human in the loop evaluation of language and embedding models.

---------------------------------------------------------------------------------------

[![Docs Status][docs-image]][docs-url]

**[Documentation](https://cheese1.readthedocs.io)**

# Getting Started

First install the required packages:
```
git clone https://github.com/carperai/cheese
cd cheese
pip install -r requirements.txt
```


You need rabbitmq for the messaging system in the backend. It can be installed easily with conda as follows:
```
conda install -c conda-forge rabbitmq-server
```
Then start the server (should do this on a different screen/window)
```
rabbitmq-server
```
Note that because of how rabbitmq works, it is possible several items may remain in the queue after your application using CHEESE has terminated. If the server is not shut down and restarted, then subsequent uses of CHEESE may end up drawing from items that were placed in the queue in a previous run.  
  
As an example, the following script runs an image selection task, where two images from LAION-art dataset are presented and the labeller is asked to choose one.
```
python -m examples.image_selection
```

# Custom tasks in Gradio
Refer to examples/image_selection.py for a comprehensive example on how to create your own custom task with a Gradio UI.
