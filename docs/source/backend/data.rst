.. _data:

BatchElements and Tasks
*************************
The components of CHEESE process data in the form of the BatchElement object. These are communicated
between the components using the Task object, which essentially serves as a container for some BatchElement.

.. autoclass:: cheese.data.BatchElement
    :members:

As an explanation for the trip attribute to BatchElement, consider the following cases. Suppose we want user to 
just label some data being read from a dataset, then write their labels to a new dataset. Then trip_max of 1
would result in the data visiting user then immediately going back to pipeline. Now suppose instead we want
user to look at data and prompt a generation from a generative model, then label the generation along with
the original data. We'd set trip_max of 3 for this since the data is visiting user, model then user again.
Once trip becomes trip_max, the data is sent back to pipeline. In the case where it is 2, then the data 
will be sent back to the pipeline from the model.

.. autoclass:: cheese.tasks.Task
    :members:
