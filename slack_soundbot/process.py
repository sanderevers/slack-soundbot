import asyncio
import logging
import traceback

class Process:
    def __init__(self):
        self.id = id(self)
        self.result = asyncio.Future()

    async def start(self,*args,**kwargs):
        asyncio.ensure_future(self._clean_run(*args,**kwargs))

    async def _clean_run(self,*args,**kwargs):
        try:
            res = await self._run(*args,**kwargs)
            self.result.set_result(res)
        except Exception as e:
            log.error('Exception in task {}:\n{}'.format(self.id,traceback.format_exc()))
            self.result.set_exception(e)

    async def _run(self):
        raise NotImplementedError('abstract!')

async def aiter(queue):
    while True:
        yield await queue.get()

log = logging.getLogger(__name__)