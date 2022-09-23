.. _customtask:

Custom Tasks in Gradio
************************

Creation of a custom task requires defining 2 or 3 new components in backend, and 1 new component in frontend.
Let's first give an example of a simple data labelling task, where we read from a dataset of text, and have a user
label each text as either positive or negative.


We first define our data, in the form of a :ref:`BatchElement <data>`. Note the default parameters of a BatchElement include client id,
trip, and an error flag. Because of the existence of default parameters in the superclass, inherited classes must also provide
default for all their values. Specifiying None suffices.

.. code-block:: python

    from cheese.data import BatchElement
    from dataclasses import dataclass

    @dataclass
    class SentimentElement(BatchElement):
        text : str = None
        label : str = None

We then create our :ref:`Pipeline <pipeline>`. Let's assume we have our dataset as an iterator over many strings. Then we
can create an IterablePipeline for this task. The IterablePipeline constructor can take an iterator
and some other parameters (which we will discuss momentarily). The abstract methods we must overide
for our new task are preprocess, fetch, and post. Preprocess is called on all new items retrieved
from the iterator. Fetch is called to construct the next BatchElement to be sent to the client.
Post is called when a BatchElement is returned from the client or the model.

While not required, in most cases you'd probably want to use IterablePipeline.fetch_next() to get the
next item from the iterator (in some cases you may want to get multiple items, so you can call it
multiple times in fetch). This method will automatically call preprocess for you. Additionally,
you will likely want to use IterablePipeline.post_row(row) to post a new row to the result dataset.
This also handles saving for you. 

.. code-block:: python

    from cheese.pipeline.iterable_dataset import IterablePipeline

    class SentimentPipeline(IterablePipeline):
        def preprocess(self, x):
            return x # Don't need any changes here- it's just a string
        
        def fetch(self) -> SentimentElement:
            return SentimentElement(text=self.fetch_next())

        def post(self, data : SentimentElement):
            row = {"text": data.text, "label": data.label}
            if not data.error: self.post_row(row)

Next we create our frontend using gradio. This will require a :ref:`GradioFront <gradio>` object. In
it we have to define main (where the UI is constructed), receive (where we get the user input and update data with it),
and present (where we display the data to the user). The important thing to note about many of these functions is that
two variables id and task (see :ref:`Task <data>`) are assumed to be passed around them. Note the usage of GradioFront.wrap_event() as a decorator
in main(). This serves to add id and task as inputs and outputs to response (the function being called with the button click).
This keeps track of the id and task for a particular client. We access the clients specific data through said task.
GradioFront.response() takes care of sending the users input to the ClientManager after it has been submitted,
which takes care of sending the data to its next target. Whatever button or method you use to submit data from the user 
should call response(). Additionally, note that main() returns a list of outputs. This is required in order for GradioFront
to be able to access the outputs and update them when we are showing the client their first task after logging in. Do 
keep in mind that main() and present() are expected to return lists, and returning single items will cause errors.

.. code-block:: python

    from cheese.client.gradio_client import GradioFront
    import gradio as gr

    class SentimentFront(GradioFront):
        def main(self):
            with gr.Column():
                txt = gr.Textbox(interactive = False, label = "Text")
                select = gr.Radio(["Positive", "Negative"], label = "Label")
                btn = gr.Button("Submit")
        
            self.wrap_event(btn.click)(
                self.response, inputs = [select], outputs = [txt]
            )

            return [txt]

        def receive(self, *inp):
            # Receive gets a list of inputs which consist of
            # [id, task, *inputs], where *inputs is the gradio inputs
            # in this case, the gradio inputs are just the radio selection
            _, task, label = inp
            task.data.label = label
            task.data.error = (label is None) # Error if the label wasn't selected

            # We can choose to raise an InvalidInputException here if we want to
            # By default, this would simply result in the same data being shown
            # to the user again.
            # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
            # result dataset

            # Receive has to return the task updated with user input
            return task

        def present(self, task):
            data : SentimentElement = task.data
            return [data.text] # Return list for gradio outputs


After the frontend has been written, we can simply startup CHEESE for our experiment. The below code snippet
will run the experiment on two strings and post the results to a folder called sentiment_result.

.. code-block:: python

    from cheese.api import CHEESE
    import time

    data = ["The goose went to the store and was very happy", "The goose went to the store and was very sad"]
    data = iter(data) # Cast to an iterator for IterablePipeline

    cheese = CHEESE(
        pipeline_cls = SentimentPipeline,
        client_cls = SentimentFront,
        gradio = True,
        pipeline_kwargs = {
            "iter" : data,
            "write_path" : "./sentiment_result",
            "force_new" : True,
            "max_length" : 5
        }
    )
    
    print(cheese.launch()) # Prints the URL

    print(cheese.create_client(1)) # Create client with ID 1 and return a user/pass for them to use

    while not cheese.finished:
        time.sleep(2)
    
    print("Done!")


Now, how about adding a model to the loop? Suppose we want a sentiment analysis model to also provide a label for each text
after a human has provided theirs, so we can later compare the sentiment analysis model to a human baseline. All that is 
required is to add some new attributes to the data (which requires us to modify the pipeline as well), and to create the model. We will make use of the trip_max attribute
to specify we want the data to go from client to the model before it goes back to the pipeline. Otherwise, the only difference
to construction of the CHEESE object is specifiying a model class. 

.. code-block:: python

    @dataclass
    class SentimentElement(BatchElement):
        text : str = None
        label : str = None
        model_label : str = None
        trip_max : int = 2 # -> Client -> Model -> Pipeline = two targets to visit before going back to pipeline
    
    from cheese.models import BaseModel
    from transformers import pipeline

    class SentimentModel(BaseModel):
        def __init__(self):
            super().__init__()

            # Use HF Transformers to create a small sentiment analysis pipeline
            self.model = pipeline("sentiment-analysis", model = "nlptown/bert-base-multilingual-uncased-sentiment")

        def process(self, data : SentimentElement) -> SentimentElement:
            txt = data.text
            label = self.model(txt)[0]["label"]
            data.model_label = label
            return data

    class SentimentPipeline(IterablePipeline):
        def preprocess(self, x):
            return x # Don't need any changes here- it's just a string
        
        def fetch(self) -> SentimentElement:
            return SentimentElement(text=self.fetch_next())

        def post(self, data : SentimentElement):
            row = {"text": data.text, "label": data.label, "model_label": data.model_label}
            if not data.error: self.post_row(row)

    cheese = CHEESE(
        pipeline_cls = SentimentPipeline,
        client_cls = SentimentFront,
        model_cls = SentimentModel,
        gradio = True,
        pipeline_kwargs = {
            "iter" : data,
            "write_path" : "./sentiment_result",
            "force_new" : True,
            "max_length" : 5
        }
    )
