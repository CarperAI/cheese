from dataclasses import dataclass

@dataclass
class BatchElement:
    """Abstract base class for BatchElements. Store all kinds of data being passed around CHEESE"""
    client_id : int = -1 # ID of the client that was assigned the data last
    trip : int = 0 # How many targets has the BatchElement visited so far?
    trip_max : int = 1 # How many targets *should* the BatchElement visit before going back to pipeline
    # Default value of 1 causes data to immediately go back to pipeline after labelling by user
    # ex: Value of 3 would allow for data to follow pipeline -> client -> model -> client -> pipeline
    error : bool = False # Used to mark bad data (i.e. when data is not properly presented to user)
