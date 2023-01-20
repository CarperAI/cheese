from cheese.data import BatchElement
from dataclasses import dataclass
from cheese.pipeline.iterable_dataset import IterablePipeline
from cheese.client.gradio_client import GradioFront
from cheese import CHEESE
import csv
from datasets import load_dataset
import gradio as gr
import time
import os


@dataclass
class CodeCritiqueElement(BatchElement):
    question_id : str = None
    question : str = None
    answer : str = None
    original_question : str = None
    original_code : str = None
    refined_code : str = None
    critique : str = None


class CodeCritiquePipeline(IterablePipeline):
    def preprocess(self, data):
        question_id = data['question_id']
        question = data['body']
        answer = data['answers'][0]['body']
        return {"question_id": question_id, "question": question, "answer": answer}

    def fetch(self) -> CodeCritiqueElement:
        next_element = self.fetch_next()
        # TODO: exit here if no element
        return CodeCritiqueElement(
            question_id=next_element["question_id"],
            question=next_element["question"],
            answer=next_element["answer"],
            original_question=next_element["question"],
            original_code=next_element["question"],
            refined_code=next_element["answer"],
            critique=next_element["answer"]
        )

    def post(self, data : CodeCritiqueElement):
        row = {
            "question_id": data.question_id,
            "question": data.question,
            "answer": data.answer,
            "original_question": data.original_question,
            "original_code": data.original_code,
            "refined_code": data.refined_code,
            "critique": data.critique,
            "cheese_client_id": data.client_id,
        }
        print("posting row: ")
        print(row)
        if not data.error: self.post_row(row)

class CodeCritiqueFront(GradioFront):
    def main(self):
        with gr.Column():
            gr.HTML("<p>Please read the annotation guidelines <a href=\"https://github.com/CarperAI/CodeReviewSE/blob/main/Annotation_Guidelines.md#annotation-guidelines-for-the-code-review-dataset\" style=\"text-decoration: underline; color: cornflowerblue;\">here</a> before participating.</p>")
            question_id = gr.Textbox(interactive = False, label = "Question ID")
            question = gr.Textbox(interactive = False, label = "Question")
            answer = gr.Textbox(interactive=False, label="Answer")
            original_question = gr.Textbox(interactive=True, label="Extract Question Text From Question")
            original_code = gr.Textbox(interactive=True, label="Extract Original Code From Question")
            refined_code = gr.Textbox(interactive=True, label="Extract Refined Code From Answer")
            critique = gr.Textbox(interactive=True, label="Extract Critique From Answer")
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response,
            inputs = [original_question, original_code, refined_code, critique],
            outputs = [question_id, question, answer, original_question, original_code, refined_code, critique]
        )

        return [question_id, question, answer, original_question, original_code, refined_code, critique]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, original_question, original_code, refined_code, critique = inp
        task.data.original_question = original_question
        task.data.original_code = original_code
        task.data.refined_code = refined_code
        task.data.critique = critique
        task.data.error = (original_code is None or refined_code is None or critique is None) # Error if the label wasn't selected

        # We can choose to raise an InvalidInputException here if we want to
        # By default, this would simply result in the same data being shown
        # to the user again.
        # For this example, we allow invalid inputs, but mark them as errors so they aren't written to
        # result dataset

        # Receive has to return the task updated with user input
        return task

    def present(self, task):
        data : CodeCritiqueElement = task.data
        return [data.question_id, data.question, data.answer, data.original_question, data.original_code, data.refined_code, data.critique] # Return list for gradio outputs

def get_file_as_dict(path):
    """
        Read a file as a dictionary
        Each line should be of the form key:value
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    d = {}
    for line in lines:
        key, value = line.split(':')
        d[key] = value
    return d


# old dataset
# dataset = load_dataset("Dahoas/code-review-instruct-critique-revision-python", split="train")
# new dataset
dataset = load_dataset("reshinthadith/2048_has_code_filtered_base_code_review_python_based_on_property", split="train")

# These 500 indexes have already been or are in the process of being annotated, and should be removed from the dataset
row_1 = ['105853', '109562', '110452', '112642', '116196', '138451', '139690', '152837', '161445', '163528', '169715', '181621', '182401', '185740', '186481', '189264', '196591', '197397', '202727', '204094', '209208', '209869', '211504', '216967', '223569', '227020', '230224', '23363', '234286', '236040', '241191', '242109', '243048', '243977', '247597', '247603', '248884', '250068', '256549', '265676', '270551', '30388', '37083', '47311', '48182', '4872', '49840', '8928', '90276', '93439']
row_2 = ['104645', '108527', '109484', '109652', '115076', '119175', '132023', '134266', '139121', '155551', '158892', '159677', '164952', '166915', '176073', '194311', '198471', '204534', '205318', '206326', '208740', '21367', '220296', '226970', '22822', '229177', '231625', '232360', '234969', '237378', '238980', '241847', '244300', '24889', '249054', '251056', '253548', '261520', '265707', '268144', '270445', '3454', '4290', '44244', '5229', '57493', '62955', '85282', '9433', '98110']
row_3 = ['102674', '11317', '131689', '133723', '140018', '151895', '155610', '158675', '17859', '179790', '194411', '195104', '200950', '20416', '20564', '205830', '206943', '208158', '213677', '213875', '216116', '217222', '225014', '225221', '227281', '227710', '229552', '231168', '231930', '243019', '244141', '248047', '250170', '251915', '259021', '261575', '266480', '28768', '2957', '48288', '51844', '58184', '59833', '68097', '78302', '83303', '87533', '94780', '9592', '98473']
row_4 = ['105441', '118197', '122970', '126100', '133514', '143307', '143869', '145512', '150324', '154374', '162988', '173105', '176840', '177041', '191795', '191861', '194727', '201483', '202222', '203700', '203842', '209462', '223471', '226209', '226455', '228969', '229071', '230180', '233702', '234846', '236865', '241487', '241658', '250090', '250463', '251359', '255989', '256197', '260585', '265990', '28647', '40784', '42420', '43175', '73554', '75710', '82432', '82784', '88645', '91496']
row_5 = ['101348', '105883', '110769', '111684', '131804', '15395', '154534', '157698', '158049', '160277', '161273', '163898', '164709', '172929', '173049', '177960', '183763', '191988', '195672', '196034', '200425', '201472', '202480', '204792', '205474', '21033', '216653', '217235', '222772', '22968', '230972', '232981', '236229', '242894', '242951', '245982', '24836', '255491', '256319', '259665', '27821', '32449', '43981', '45458', '5548', '57715', '60540', '70989', '88783', '94776']


previously_collected_ids = []

# also exclude questions that have already been labeled (question_id exists in our output dataset)
# so that if the server is restarted, we resume where we left off
if os.path.isfile("./code_critique_result.csv"):
    with open("./code_critique_result.csv", 'r') as data:
        for line in csv.reader(data):
            completed_question_id = line[0]
            previously_collected_ids.append(completed_question_id)
    # remove csv header
    previously_collected_ids.remove(previously_collected_ids[0])
    print("length of previously_collected_ids", len(previously_collected_ids))
    print("previously_collected_ids", previously_collected_ids)

ignore_question_ids = row_1 + row_2 + row_3 + row_4 + row_5 + previously_collected_ids

# what we don't want
exclude_idx = []

for idx, row in enumerate(dataset):
    for ignore_question_id in ignore_question_ids:
        if row["question_id"] == ignore_question_id:
            exclude_idx.append(idx)


# create new dataset excluding those idx
filtered_dataset = dataset.select(
    (
        i for i in range(len(dataset))
        if i not in set(exclude_idx)
    )
)

print("length of dataset: ", len(dataset))
print("length of filtered dataset: ", len(filtered_dataset))

shuffled_filtered_dataset = filtered_dataset.shuffle(seed=43)

data = iter(shuffled_filtered_dataset) # Cast to an iterator for IterablePipeline

if __name__ == "__main__":
    cheese = CHEESE(
        pipeline_cls = CodeCritiquePipeline,
        client_cls = CodeCritiqueFront,
        gradio = True,
        no_login = True,
        pipeline_kwargs = {
            "iter" : data,
            "write_path" : "./code_critique_result.csv",
            "force_new" : False,
        }
    )

    cheese.launch()
    cheese.start_listening()
