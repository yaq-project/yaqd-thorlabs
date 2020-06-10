import asyncio
import re

from yaqd_core import aserial, logging

logger = logging.getLogger("serial")


class SerialDispatcher:
    def __init__(self, port):
        self.port = port
        self.workers = {}
        self.write_queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()
        self.tasks = [
            self.loop.create_task(self.do_writes()),
            self.loop.create_task(self.read_dispatch()),
        ]

    def write(self, data):
        self.write_queue.put_nowait(data)

    async def do_writes(self):
        while True:
            data = await self.write_queue.get()
            self.port.write(data)
            self.write_queue.task_done()

    async def read_dispatch(self):
        import thorlabs_apt_protocol as apt  # type: ignore

        unpacker = apt.Unpacker(self.port)
        async for msg in unpacker:
            if msg.source in self.workers:
                self.workers[msg.source].put_nowait(msg)
            else:
                logger.error(f"Unexpected reply: {msg}")
            await asyncio.sleep(0)

    def flush(self):
        self.port.flush()

    def close(self):
        self.loop.create_task(self._close())

    async def _close(self):
        for task in self.tasks:
            task.cancel()
