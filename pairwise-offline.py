from cheese import CHEESE
from cheese.data import BatchElement
from cheese.pipeline.iterable_dataset import IterablePipeline
from cheese.client.gradio_client import GradioFront, InvalidInputException
import csv
from dataclasses import dataclass
from datasets import load_dataset
import gradio as gr
import time
import random
import os


@dataclass
class PairwiseOfflineElement(BatchElement):
    original_dataset_index : str = None
    prompt : str = None
    first_output : str = None
    first_output_correctness : str = None
    first_output_responsiveness : str = None
    first_output_harmfulness : str = None
    second_output : str = None
    second_output_correctness : str = None
    second_output_responsiveness : str = None
    second_output_harmfulness : str = None
    label : str = None
    label_explanation : str = None
    swapped : str = None


class PairwiseOfflinePipeline(IterablePipeline):
    def preprocess(self, row):
        # remove "prompt" object nesting
        row['first_output'] = row['first_output']['response']
        row['second_output'] = row['second_output']['response']
        return row

    def fetch(self) -> PairwiseOfflineElement:
        next_element = self.fetch_next()
        # TODO: exit here if no element
        return PairwiseOfflineElement(
            prompt=next_element["prompt"],
            first_output=next_element["first_output"],
            second_output=next_element["second_output"],
        )

    def swap(self, a, b):
        temp = a
        a = b
        b = temp
        return a, b

    def post(self, data : PairwiseOfflineElement):
        if data.swapped == "True":
            data.first_output, data.second_output = self.swap(data.first_output, data.second_output)
            data.first_output_correctness, data.second_output_correctness = self.swap(data.first_output_correctness, data.second_output_correctness)
            data.first_output_responsiveness, data.second_output_responsiveness = self.swap(data.first_output_responsiveness, data.second_output_responsiveness)
            data.first_output_harmfulness, data.second_output_harmfulness = self.swap(data.first_output_harmfulness, data.second_output_harmfulness)
            swapped_label = ""
            if data.label == "Response A is better.":
                swapped_label = "Response B is better."
            elif data.label == "Response B is better.":
                swapped_label = "Response A is better."
            data.label = swapped_label

        row = {
            "original_dataset_index": data.original_dataset_index,
            "prompt": data.prompt,
            "first_output": data.first_output,
            "first_output_correctness": data.first_output_correctness,
            "first_output_responsiveness": data.first_output_responsiveness,
            "first_output_harmfulness": data.first_output_harmfulness,
            "second_output": data.second_output,
            "second_output_correctness": data.second_output_correctness,
            "second_output_responsiveness": data.second_output_responsiveness,
            "second_output_harmfulness": data.second_output_harmfulness,
            "label": data.label,
            "label_explanation" : data.label_explanation,
            "cheese_client_id": data.client_id,
            "elapsed_seconds": float(data.end_time) - float(data.start_time),
        }
        print("posting row: ")
        print(row)
        if not data.error: self.add_row_to_dataset(row)


class PairwiseOfflineFront(GradioFront):
    def main(self):
        with gr.Column():
            html_headline = gr.HTML("<p style=\"font-size: larger;\">Please read the study instructions <a href=\"https://docs.google.com/document/d/1R8RTZPClxe_4MwXX4B_BgcFgnbv1ynjZatVr3c7YmUo/edit\" style=\"text-decoration: underline; color: cornflowerblue;\">here</a> before participating.</p>")
        with gr.Column():
            prompt = gr.Textbox(label = "Dialogue with an AI Assistant")
        with gr.Column():
            html_description = gr.HTML("<p>Two possible responses from the AI are listed below</p>")
        with gr.Column():
            first_output = gr.Textbox(label = "Response A")
            first_output_correctness = gr.Radio(
                choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"],
                label = "Is this response correct?*"
            )
            first_output_responsiveness = gr.Radio(
                choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"],
                label = "How responsive is this response to answering the prompt?*"
            )
            first_output_harmfulness = gr.Radio(
                choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"],
                label = "Is this response harmful?*"
            )
        with gr.Column():
            second_output = gr.Textbox(label = "Response B")
            second_output_correctness = gr.Radio(
                choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"],
                label = "Is this response correct?*"
            )
            second_output_responsiveness = gr.Radio(
                choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"],
                label = "How responsive is this response to answering the prompt?*"
            )
            second_output_harmfulness = gr.Radio(
                choices = ["disagree", "mostly disagree", "unsure", "mostly agree", "agree"],
                label = "Is this response harmful?*"
            )
        with gr.Column():
            label = gr.Radio(["Response A is better.", "Response B is better."], label = "Which of the two responses is most helpful towards addressing the prompt?*", visible = True)
            label_explanation = gr.Textbox(label="Please explain why the response you chose is more helpful.*", visible=False, value=None)
        with gr.Column():
            button = gr.Button("Submit")

        self.wrap_event(button.click)(
            self.response,
            inputs = [
                first_output_correctness,
                first_output_responsiveness,
                first_output_harmfulness,
                second_output_correctness,
                second_output_responsiveness,
                second_output_harmfulness,
                label,
                label_explanation
            ],
            outputs = [
                html_headline,
                prompt,
                html_description,
                first_output,
                first_output_correctness,
                first_output_responsiveness,
                first_output_harmfulness,
                second_output,
                second_output_correctness,
                second_output_responsiveness,
                second_output_harmfulness,
                label,
                label_explanation,
                button
            ]
        )

        return [
            html_headline,
            prompt,
            html_description,
            first_output,
            first_output_correctness,
            first_output_responsiveness,
            first_output_harmfulness,
            second_output,
            second_output_correctness,
            second_output_responsiveness,
            second_output_harmfulness,
            label,
            label_explanation,
            button
        ]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, first_output_correctness, first_output_responsiveness, first_output_harmfulness, second_output_correctness, second_output_responsiveness, second_output_harmfulness, label, label_explanation = inp
        task.data.first_output_correctness = first_output_correctness
        task.data.first_output_responsiveness = first_output_responsiveness
        task.data.first_output_harmfulness = first_output_harmfulness
        task.data.second_output_correctness = second_output_correctness
        task.data.second_output_responsiveness = second_output_responsiveness
        task.data.second_output_harmfulness = second_output_harmfulness
        task.data.label = label
        task.data.label_explanation = label_explanation

        task.data.error = (
                first_output_correctness is None or
                first_output_responsiveness is None or
                first_output_harmfulness is None or
                second_output_correctness is None or
                second_output_responsiveness is None or
                second_output_harmfulness is None or
                label is None
        ) # Error if the inputs haven't been selected

        # if task.data.error:
        #     raise InvalidInputException(*inp)

        # We can choose to raise an InvalidInputException here if we want to
        # By default, this would simply result in the same data being shown
        # to the user again.
        # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
        # result dataset

        # Receive has to return the task updated with user input
        return task

    def present(self, task):
        data : PairwiseOfflineElement = task.data

        if random.randint(0, 5) == 0:
            data.label_explanation = gr.update(visible=True)
        else:
            data.label_explanation = gr.update(visible=False)

        study_has_ended = False
        if study_has_ended == True:
            data.html_headline = gr.update(visible=False)
            data.prompt = gr.update(visible=False)
            data.html_description = gr.update(value="<p style=\"font-size: larger; text-align: center;\">You have completed the study. Your prolific code is: SBR-839.</p>")
            data.first_output = gr.update(visible=False)
            data.first_output_correctness = gr.update(visible=False)
            data.first_output_responsiveness = gr.update(visible=False)
            data.first_output_harmfulness = gr.update(visible=False)
            data.second_output = gr.update(visible=False)
            data.second_output_correctness = gr.update(visible=False)
            data.second_output_responsiveness = gr.update(visible=False)
            data.second_output_harmfulness = gr.update(visible=False)
            data.label = gr.update(visible=False)
            data.label_explanation = gr.update(visible=False)
            data.button = gr.update(visible=False)
        else:
            data.html_headline = gr.update(visible=True)
            data.html_description = gr.update(visible=True)
            data.button = gr.update(visible=True)

        return [
            data.html_headline,
            data.prompt,
            data.html_description,
            data.first_output,
            data.first_output_correctness,
            data.first_output_responsiveness,
            data.first_output_harmfulness,
            data.second_output,
            data.second_output_correctness,
            data.second_output_responsiveness,
            data.second_output_harmfulness,
            data.label,
            data.label_explanation,
            data.button
        ] # Return list for gradio outputs


random.seed(43)

# Synthetic Anthropic Helpful Static Dataset****
# For these tasks, half of the prompts are natural, half are synthetic.

# 125M
# dataset = load_dataset("Dahoas/125M_hybrid_comparison", split="train")
# result_filepath = "./125M_hybrid_comparison_result.csv"
# dataset = dataset.rename_column("125M", "first_output")
# dataset = dataset.rename_column("125M_synthetic", "second_output")

# 1B
# dataset = load_dataset("Dahoas/1B_hybrid_comparison", split="train")
# result_filepath = "./1B_hybrid_comparison_result.csv"
# dataset = dataset.rename_column("1B", "first_output")
# dataset = dataset.rename_column("1B_synthetic", "second_output")

# 6B
# dataset = load_dataset("Dahoas/6B_hybrid_comparison", split="train")
# result_filepath = "./6B_hybrid_comparison_result.csv"
# dataset = dataset.rename_column("6B", "first_output")
# dataset = dataset.rename_column("6B_synthetic", "second_output")

# 20B
dataset = load_dataset("Dahoas/20B_hybrid_comparison", split="train")
result_filepath = "./20B_hybrid_comparison_result.csv"
dataset = dataset.rename_column("20B", "first_output")
dataset = dataset.rename_column("20B_synthetic", "second_output")


# add original index to rows
def add_row_index_column(row, idx):
    row["original_dataset_index"] = idx
    return row


dataset = dataset.map(add_row_index_column, with_indices=True)


# shuffle columns with seed
def shuffle_columns(row):
    if (random.randint(0,1) >= 1):
        row["swapped"] = True
        temp = row["first_output"]
        row["first_output"] = row["second_output"]
        row["second_output"] = temp
    else:
        row["swapped"] = False
    return row


dataset = dataset.map(shuffle_columns)


# skip previously completed entries
original_dataset_indices_to_exclude = []
if os.path.isfile(result_filepath):
    with open(result_filepath, 'r') as data:
        for line in csv.reader(data):
            original_dataset_index = line[0]
            original_dataset_indices_to_exclude.append(original_dataset_index)

# create new dataset excluding those idx
dataset = dataset.select((
        i for i in range(len(dataset))
        if i not in set(original_dataset_indices_to_exclude)
    ))


# TODO: display end of study code after 30min of feedback collection

# TODO: read prolific IDs from URL parameters

data = iter(dataset) # Cast to an iterator for IterablePipeline

if __name__ == "__main__":
    cheese = CHEESE(
        pipeline_cls = PairwiseOfflinePipeline,
        client_cls = PairwiseOfflineFront,
        gradio = True,
        pipeline_kwargs = {
            "iter" : data,
            "write_path" : result_filepath,
            "force_new" : False
        }
    )

    print(cheese.launch()) # Prints the URL

    # create 40 test users from the pre-generated cheese_users.csv db
    with open("./cheese_users.csv", 'r') as data:
        for line in csv.reader(data):
            print(cheese.create_client(int(line[0]), int(line[1])))

    cheese.start_listening()
    exit()
