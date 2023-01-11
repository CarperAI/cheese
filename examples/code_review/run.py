from cheese import CHEESE
from examples.code_review.code_critique import CodeCritiquePipeline, CodeCritiqueFront
import time

data = [
    {"question": "The goose went to the store and was very happy", "answer": "Positive sentiment."},
    {"question": "The goose went to the store and was very sad", "answer": "Negative sentiment."}
]
data = iter(data) # Cast to an iterator for IterablePipeline

cheese = CHEESE(
    pipeline_cls = CodeCritiquePipeline,
    client_cls = CodeCritiqueFront,
    gradio = True,
    pipeline_kwargs = {
        "iter" : data,
        "write_path" : "./code_critique",
        "force_new" : True,
        "max_length" : 5
    }
)

print(cheese.launch()) # Prints the URL

print(cheese.create_client(1)) # Create client with ID 1 and return a user/pass for them to use

while not cheese.finished:
    time.sleep(2)

print("Done!")
