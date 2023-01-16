from cheese import CHEESE
from examples.image_selection import *

if __name__ == "__main__":
    cheese = CHEESE(
        ImageSelectionPipeline, ImageSelectionFront,
        pipeline_kwargs = {
            "iter" : make_iter(), "write_path" : "./img_dataset_res", "force_new" : True, "max_length" : 999
        },
        debug = True,
        no_login = True
    )
    cheese.launch()
    cheese.start_listening()
