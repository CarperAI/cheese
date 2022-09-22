from dataclasses import dataclass

@dataclass
class BatchElement:
    """
    Abstract base class for BatchElements. Store all kinds of data being passed around CHEESE
    
    :param client_id: The ID of the last client that touched this data
    :type client_id: int

    :param trip: How many targets have touched/accessed this data so far
    :type trip: int

    :param trip_max: How many targets can touch/access this data before it goes back to pipeline to be posted
    :type trip_max: int

    :param error: A flag for frontend to mark the data as being erroneous (i.e. if it couldn't be labelled properly)
    :type error: bool
    """
    client_id : int = -1
    trip : int = 0 
    trip_max : int = 1 
    error : bool = False 
