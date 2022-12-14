.. _faq:

FAQ
********
Q: What is CHEESE? 

A: CHEESE is an open source platform for annotation and feedback.

Q: What makes CHEESE different from other annotation tools? 

A: CHEESE was designed for use in RLHF (Reinforcement Learning from Human Feedback).  
This means it can be used in online setups where the agent requires human feedback in real time. 
Additionally, we hope to use it to perform model assisted labelling, wherein an assisting model
assists a human in providing feedback for the main model. 

Q: How do I run CHEESE? 

A: You can refer to :ref:`getting started <started>` to get CHEESE running. For more info on
creating your own tasks in CHEESE you can refer to :ref:`custom tasks in gradio <customtask>`.  

Q: Does the server have to be run from my application?

A: Nope! There are many use cases in which you may want to run CHEESE separately from your application that you wish to connect to CHEESE.
This is the purpose of :code:`cheese.api`. You can the server as you would normally, then you can call upon
the :code:`cheese.api.CHEESEAPI` object to use any of the functionality of :code:`cheese.CHEESE`.


