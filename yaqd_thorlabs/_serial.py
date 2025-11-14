import asyncio
import re

from yaqd_core import aserial, logging

logger = logging.getLogger("serial")


class SerialDispatcher:
    def __init__(self, port):
        self.port = port
        self.workers = {}
        self.write_queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
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
            await asyncio.sleep(0.01)

    async def read_dispatch(self):
        raise NotImplementedError

    def flush(self):
        self.port.flush()

    def close(self):
        self.loop.create_task(self._close())

    async def _close(self):
        await self.write_queue.join()
        for worker in self.workers.values():
            await worker.join()
        for task in self.tasks:
            task.cancel()


class SerialDispatcherApt(SerialDispatcher):
    async def read_dispatch(self):
        import thorlabs_apt_protocol as apt  # type: ignore

        unpacker = apt.Unpacker(self.port)
        async for msg in unpacker:
            sent = 0
            for key, worker in self.workers.items():
                source, chan_ident = key
                if source != msg.source:
                    continue
                if hasattr(msg, "chan_ident") and msg.chan_ident != chan_ident:
                    continue
                worker.put_nowait(msg)
                sent += 1
            if not sent:
                logger.error(f"Unexpected reply: {msg}")
            await asyncio.sleep(0)


class SerialDispatcherEll(SerialDispatcher):
    async def read_dispatch(self):
        parse = re.compile(rb"^([0-9a-fA-F])([A-Za-z0-9][A-Za-z0-9])([ -~]*)$")
        async for line in self.port.areadlines():
            line = re.sub(rb"\s", b"", line.strip())
            match = parse.match(line)
            if match is None:
                logger.error(f"No match for {line}")
                continue
            index, command, args = match.groups()
            index = int(index, 16)
            if index in self.workers:
                self.workers[index].put_nowait((command.decode(), args.decode()))
            else:
                logger.error(f"no worker {index}")
