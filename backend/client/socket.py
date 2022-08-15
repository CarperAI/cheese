import asyncio
import json
import threading
import websockets
from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, Optional

from backend.utils.thread_utils import synchronized
from backend.utils.json_utils import dataclass_to_json

@dataclass
class Message:
    type : str
    payload : Optional[Dict[str, Any]] = None

class ClientSocket:
    def __init__(self, port, mgr):
        self.port = port
        self.connected = set()
        self.send_queues = {}
        self.mgr = mgr
        self.mgr_lock = self.mgr.client_list_lock
        self.loop = asyncio.new_event_loop()

    def notify_task_is_ready(self, client_id):
        asyncio.run_coroutine_threadsafe(
            self.__notify_task_is_ready(client_id),
            self.loop,
        )

    async def __notify_task_is_ready(self, client_id):
        if client_id in self.send_queues:
            await self.send_queues[client_id].put(Message("task_available"))

    @synchronized("mgr_lock")
    def __handle_ready(self, client_id : int) -> Message:
        front = self.mgr.clients[client_id].front
        if front.refresh():
            return Message(
                type="new_task",
                payload=front.data,
            )
        return Message("idle")

    @synchronized("mgr_lock")
    def __handle_complete(self, client_id : int, payload : Dict[str, Any]) -> Message:
        front = self.mgr.clients[client_id].front
        if front.on_submit(payload):
            return Message("task_available")
        return None

    @synchronized("mgr_lock")
    def __check_valid_client_id(self, client_id) -> int:
        if client_id not in self.mgr.clients:
            raise ValueError(f"No client with ID {client_id}!")
        if client_id in self.connected:
            raise ValueError(f"Client {client_id} is already connected somewhere else!")

        return client_id

    def __handle_msg(self, client_id : int, msg : Message):
        if msg.type == "ready":
            return self.__handle_ready(client_id)
        elif msg.type == "complete":
            return self.__handle_complete(client_id, msg.payload)
        else:
            raise ValueError("Unknown message type")

    async def __message_loop(self, socket, client_id : str):
        recv_task = asyncio.create_task(socket.recv())
        send_task = asyncio.create_task(self.send_queues[client_id].get())
        while True:
            done, _ = await asyncio.wait(
                { recv_task, send_task },
                return_when=asyncio.FIRST_COMPLETED,
            )

            if recv_task in done:
                message_json = await recv_task
                message = Message(**json.loads(message_json))
                reply = self.__handle_msg(client_id, message)
                if reply is not None:
                    await socket.send(dataclass_to_json(reply))
                recv_task = asyncio.create_task(socket.recv())

            if send_task in done:
                message = await send_task
                await socket.send(dataclass_to_json(message))
                send_task = asyncio.create_task(self.send_queues[client_id].get())

    async def __new_connection(self, socket, path):
        if not path.startswith("/client"):
            raise ValueError(f"Unknown path {path}!")

        client_id = None
        try:
            client_id = self.__check_valid_client_id(
                int(path.replace("/client/", ""))
            )
            self.connected.add(client_id)
            self.send_queues[client_id] = asyncio.Queue()
            print(f"Client {client_id} is now connected.")

            await socket.send(dataclass_to_json(Message("ready")))
            await self.__message_loop(socket, client_id)
        except websockets.exceptions.ConnectionClosedOK:
            # Client closed the connection.
            pass
        except Exception as ex:
            await socket.send(dataclass_to_json(Message("error", str(ex))))
        finally:
            if client_id is not None:
                print(f"Client {client_id} has disconnected.")
                self.connected.discard(client_id)


    def __run(self):
        asyncio.set_event_loop(self.loop)

        start_server = websockets.serve(
            self.__new_connection,
            "localhost",
            self.port,
        )
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    def start(self):
        threading.Thread(target=self.__run).start()
