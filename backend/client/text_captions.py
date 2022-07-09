from backend.client import Client
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.data.text_captions import TextCaptionBatchElement

import gradio as gr

class TextCaptionClient(Client):
    def __init__(self, id : int):
        super(Client, self).__init__(self.id)

        self.front = None

    def push_task(self, task : Task):
        try:
            assert self.front is not None
        except:
            raise Exception("Error: Pushed task to frontend before it was initialized")
        
        data : TextCaptionBatchElement  = task.data
        self.front.data = {
            "text" : data.text,
            "captions" : data.captions,
            "caption_inds" : data.caption_index
        }


    def init_front(self) -> str:
        default_data = {
            "text" : "This is my amazing story about a fox." +  \
                    "The fox was brown. It was also renowned for being quick." + \
                    "It proved its talents by jumping over a dog. It just so happened that this dog was lazy. This cemented it as being the quick brown fox that jumped over the lazy dog.",
            "captions" : [],
            "caption_inds" : [],
        }
        self.front = TextCaptionFront(default_data)       
        
class TextCaptionFront:
    def __init__(self, data):
        self.data = data
        self.demo = gr.Interface(
            fn = self.response,
            inputs = ["text"],
            outputs = [gr.Textbox(placeholder = ph[0]),
                       gr.Textbox(placeholder = ph[1])
                    ],
        )

    def generate_str(self):
        # generate a string from data using caption indexes
        res = self.data["text"]

        i = len(self.data["captions"]) - 1
        for inds in reversed(self.data["caption_inds"]):
            res = res[:inds[0]] + f"[{i}][" + res[inds[0]:inds[1]] + "]" + res[inds[1]:]
            i -= 1

        res_captions = ""
        for i, caption in enumerate(self.data["captions"]):
            res_captions += f"{i}: {caption}\n"

        return res, res_captions

    def response(self, inp):
        # Parse input line by line
        lines = inp.split("\n")
        # First two integers are character positions for caption
        indices = [[int(x) for x in line.split(" ")[:2]] \
                    for line in lines]
        
        # rest is caption
        captions = [" ".join(line.split(" ")[2:]) for line in lines]

        self.data["captions"] += captions
        self.data["caption_inds"] += indices

        return self.generate_str()


    def get_demo(self):
        ph = self.generate_str()
        demo = gr.Interface(
            fn = self.response,
            inputs = ["text"],
            outputs = [gr.Textbox(placeholder = ph[0]),
                       gr.Textbox(placeholder = ph[1])
                    ],
        )
        return demo


