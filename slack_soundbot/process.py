import asyncio

class Process:
    async def start(self):
        asyncio.ensure_future(self._run())
    async def _run(self):
        raise NotImplementedError('abstract!')

async def aiter(queue):
    while True:
        yield await queue.get()
