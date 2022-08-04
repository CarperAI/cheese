from typing import Any, Dict, Optional

from backend.client import Client, ClientFront
from backend.tasks import Task
from backend.client.states import ClientState as CS
from backend.data.text_captions import TextCaptionBatchElement
from backend.utils.thread_utils import (
    runs_in_socket_thread,
    synchronized,
)

class TextCaptionClient(Client):
    def init_front(self) -> str:
        return super().init_front(TextCaptionFront)

class TextCaptionFront(ClientFront):
    @synchronized("member_lock")
    @runs_in_socket_thread
    def on_submit(self, inp : Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Take input from user and gives a response for them to see. If they are being shown a task,
        takes their input as being a caption. Otherwise, ignores the input but refreshes and tries to get a new task.
        """
        if self.showing_data:
            # If they were seeing data and pressed button,
            # we assume they made captions and are now submitting

            self.data.captions += inp["captions"]
            self.data.caption_index += inp["caption_index"]

            self.complete_task()
            return False

        # Otherwise if they pressed submit while seeing nothing,
        # they need to be shown their new task
        # If its ready, show it
        return self.refresh()
