import pandas as pd
from datasets import Dataset

df = pd.DataFrame(["The goose swam to the shore.", "The goose took a nap.", "Then the goose swam away."], columns = ["text"])
dataset = Dataset.from_pandas(df)
dataset.save_to_disk("dataset")
