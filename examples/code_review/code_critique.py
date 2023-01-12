from cheese.data import BatchElement
from dataclasses import dataclass

@dataclass
class CodeCritiqueElement(BatchElement):
    question : str = None
    answer : str = None
    original_code : str = None
    refined_code : str = None
    critique : str = None

from cheese.pipeline.iterable_dataset import IterablePipeline

class CodeCritiquePipeline(IterablePipeline):
    def preprocess(self, data):
        question = data['body']
        answer = data['answer']['body']
        return {"question": question, "answer": answer}

    def fetch(self) -> CodeCritiqueElement:
        next_element = self.fetch_next()
        # TODO: exit here if no element
        return CodeCritiqueElement(
            question=next_element["question"],
            answer=next_element["answer"],
            original_code=next_element["question"],
            refined_code=next_element["answer"],
            critique=next_element["answer"]
        )

    def post(self, data : CodeCritiqueElement):
        row = {
            "question": data.question,
            "answer": data.answer,
            "original_code": data.original_code,
            "refined_code": data.refined_code,
            "critique": data.critique
        }
        print("posting row: ")
        print(row)
        if not data.error: self.post_row(row)

from cheese.client.gradio_client import GradioFront
import gradio as gr

class CodeCritiqueFront(GradioFront):
    def main(self):
        with gr.Column():
            question = gr.Textbox(interactive = False, label = "Question")
            answer = gr.Textbox(interactive=False, label="Answer")
            original_code = gr.Textbox(interactive=True, label="Extract Original Code From Question")
            refined_code = gr.Textbox(interactive=True, label="Extract Refined Code From Answer")
            critique = gr.Textbox(interactive=True, label="Extract Critique From Answer")
            btn = gr.Button("Submit")

        self.wrap_event(btn.click)(
            self.response,
            inputs = [original_code, refined_code, critique],
            outputs = [question, answer, original_code, refined_code, critique]
        )

        return [question, answer, original_code, refined_code, critique]

    def receive(self, *inp):
        # Receive gets a list of inputs which consist of
        # [id, task, *inputs], where *inputs is the gradio inputs
        # in this case, the gradio inputs are just the radio selection
        _, task, original_code, refined_code, critique = inp
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
        return [data.question, data.answer, data.original_code, data.refined_code, data.critique] # Return list for gradio outputs

import time
from cheese import CHEESE
from datasets import load_dataset

dataset = load_dataset("Dahoas/code-review-instruct-critique-revision-python", split="train")
#dataset = load_dataset("Dahoas/base_code_review", split="train")

# These 500 indexes have already been or are in the process of being annotated, and should be removed from the dataset
row_1 = ['105853', '109562', '110452', '112642', '116196', '138451', '139690', '152837', '161445', '163528', '169715', '181621', '182401', '185740', '186481', '189264', '196591', '197397', '202727', '204094', '209208', '209869', '211504', '216967', '223569', '227020', '230224', '23363', '234286', '236040', '241191', '242109', '243048', '243977', '247597', '247603', '248884', '250068', '256549', '265676', '270551', '30388', '37083', '47311', '48182', '4872', '49840', '8928', '90276', '93439']
row_2 = ['104645', '108527', '109484', '109652', '115076', '119175', '132023', '134266', '139121', '155551', '158892', '159677', '164952', '166915', '176073', '194311', '198471', '204534', '205318', '206326', '208740', '21367', '220296', '226970', '22822', '229177', '231625', '232360', '234969', '237378', '238980', '241847', '244300', '24889', '249054', '251056', '253548', '261520', '265707', '268144', '270445', '3454', '4290', '44244', '5229', '57493', '62955', '85282', '9433', '98110']
row_3 = ['102674', '11317', '131689', '133723', '140018', '151895', '155610', '158675', '17859', '179790', '194411', '195104', '200950', '20416', '20564', '205830', '206943', '208158', '213677', '213875', '216116', '217222', '225014', '225221', '227281', '227710', '229552', '231168', '231930', '243019', '244141', '248047', '250170', '251915', '259021', '261575', '266480', '28768', '2957', '48288', '51844', '58184', '59833', '68097', '78302', '83303', '87533', '94780', '9592', '98473']
row_4 = ['105441', '118197', '122970', '126100', '133514', '143307', '143869', '145512', '150324', '154374', '162988', '173105', '176840', '177041', '191795', '191861', '194727', '201483', '202222', '203700', '203842', '209462', '223471', '226209', '226455', '228969', '229071', '230180', '233702', '234846', '236865', '241487', '241658', '250090', '250463', '251359', '255989', '256197', '260585', '265990', '28647', '40784', '42420', '43175', '73554', '75710', '82432', '82784', '88645', '91496']
row_5 = ['101348', '105883', '110769', '111684', '131804', '15395', '154534', '157698', '158049', '160277', '161273', '163898', '164709', '172929', '173049', '177960', '183763', '191988', '195672', '196034', '200425', '201472', '202480', '204792', '205474', '21033', '216653', '217235', '222772', '22968', '230972', '232981', '236229', '242894', '242951', '245982', '24836', '255491', '256319', '259665', '27821', '32449', '43981', '45458', '5548', '57715', '60540', '70989', '88783', '94776']
row_6 = ['104929', '114537', '124609', '141250', '149015', '154975', '165101', '178490', '182194', '183709', '184423', '187867', '188167', '190956', '201408', '209028', '210012', '212270', '212565', '213470', '221119', '221241', '224849', '225248', '232601', '236252', '237476', '239653', '245378', '251469', '253244', '254694', '255699', '256194', '256966', '257039', '264044', '268307', '270063', '270226', '30400', '31514', '33919', '43709', '46463', '4920', '57243', '58535', '73685', '86743']
row_7 = ['110587', '113990', '125781', '127787', '129899', '132343', '133437', '136376', '143837', '148181', '149306', '162130', '162532', '164205', '172852', '179550', '205376', '210070', '210466', '211571', '211766', '221630', '224714', '226369', '232288', '234669', '238728', '241909', '242460', '248234', '250041', '253493', '259954', '260704', '261128', '263745', '32400', '40067', '47170', '56979', '59804', '60510', '66961', '68127', '7317', '81770', '81880', '87586', '88307', '93348']
row_8 = ['102335', '106393', '111155', '111516', '126211', '132394', '134427', '143470', '151116', '151806', '15219', '162745', '163752', '169648', '169711', '173024', '180543', '191926', '193371', '194598', '202753', '212276', '215852', '220940', '221725', '221930', '225119', '229921', '23180', '236739', '236879', '237601', '239217', '239338', '245438', '246002', '246160', '253628', '254721', '26008', '261013', '269428', '270567', '28985', '39270', '54935', '69813', '75535', '82165', '93546']
row_9 = ['107033', '108057', '125263', '129412', '131765', '142734', '145033', '149867', '159183', '159427', '160931', '161321', '163195', '168795', '169349', '173588', '180429', '185693', '186181', '187150', '190554', '192944', '193505', '200094', '205666', '209327', '212599', '217008', '219477', '221325', '223910', '230024', '230446', '230691', '233288', '239982', '266124', '32894', '37698', '40466', '445', '62065', '69099', '79393', '83225', '8358', '88407', '92489', '92648', '98983']
row_10 = ['107413', '111266', '121584', '124278', '1419', '148322', '166670', '171701', '174946', '175177', '180287', '181690', '188464', '197153', '19886', '206663', '215243', '215893', '220072', '229381', '231963', '234478', '238526', '238769', '239535', '242715', '243132', '244429', '24657', '252065', '253252', '254745', '260449', '260653', '262868', '28674', '31007', '31678', '32610', '35155', '41433', '42792', '46993', '57903', '63015', '68389', '68662', '7423', '78586', '87460']

ignore_question_ids = row_1 + row_2 + row_3 + row_4 + row_5 + row_6 + row_7 + row_8 + row_9 + row_10

# what we don't want
exclude_idx = []

for idx, row in enumerate(dataset):
    for ignore_question_id in ignore_question_ids:
        if row["question_id"] == ignore_question_id:
            exclude_idx.append(idx)
            print(idx, row["question_id"])

print(exclude_idx)


# create new dataset excluding those idx
filtered_dataset = dataset.select(
    (
        i for i in range(len(dataset))
        if i not in set(exclude_idx)
    )
)

# TODO: shuffle rows of filtered dataset


print(len(dataset))
print(len(filtered_dataset))

data = iter(dataset) # Cast to an iterator for IterablePipeline

cheese = CHEESE(
    pipeline_cls = CodeCritiquePipeline,
    client_cls = CodeCritiqueFront,
    gradio = True,
    pipeline_kwargs = {
        "iter" : data,
        "write_path" : "./code_critique_result.csv",
        "force_new" : False,
        "max_length" : 5
    }
)

print(cheese.launch()) # Prints the URL

for i in range(1, 41):
    print(cheese.create_client(i)) # Create client with ID 1 and return a user/pass for them to use

while not cheese.finished:
    time.sleep(2)

print("Done!")
