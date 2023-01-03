.. _started:

Getting Started With CHEESE
*******************************
First, clone the repo and install the requirements:  

.. code-block:: bash

    git clone https://github.com/carperai/cheese
    cd cheese
    pip install -r requirements.txt

You will also need to setup and run a rabbitmq-server for the backend to use (ideally on a different
screen from the one you plan to use CHEESE on).
This can be done as follows if you are using conda:

.. code-block:: bash

    conda install -c conda-forge rabbitmq-server
    rabbitmq-server

Then, to verify CHEESE is working, run one of the example scripts:

.. code-block:: bash

    python -m examples.image_selection

The above example script will give you a url as well as a client id and password pair to login at that url.
When logged in, the example task will be to select between one image or another 
from the `LAION-art <https://huggingface.co/datasets/laion/laion-art>`_ dataset. You may also refer
to `the script itself <https://github.com/CarperAI/cheese/blob/main/examples/image_selection.py>`_ for
a well documented example on setting up a custom task for CHEESE. For more details
on creating your own custom tasks in CHEESE, refer to :ref:`custom tasks in gradio <customtask>`.
