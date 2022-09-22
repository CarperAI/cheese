.. _gradio:

Clients and Frontends
******************************

The basic ClientManager can support any kind of frontend or client. 
However, writing your own frontend may not be the fastest path to running your experiment with CHEESE.
It is reccomended to instead use the GradioClientManager and to create your frontend in Gradio.
If you should choose to do this, the GradioFront object is all you will need for the frontend of your experiment.

.. autoclass:: cheese.client.ClientManager
    :members:

.. autoclass:: cheese.client.gradio_client.GradioClientManager
    :members:

.. autoclass:: cheese.client.gradio_client.GradioFront
    :members:
