import logging
import asyncio
from .config import Config
from .process import Process, aiter

class Ret:
    played = object()
    interrupted = object()
    notfound = object()
    unknown = object()

class PlayRun(Process):
    def __init__(self, filename):
        self.process = None
        self.filename = filename
        self.ended = asyncio.Future()

    async def _run(self):
        self.process = await asyncio.create_subprocess_exec(Config.play_cmd, self.filename)
        returncode = await self.process.wait()
        log.debug('PlayRun {} ended in {}'.format(self.filename, returncode))
        self.process = None
        self.ended.set_result(self.ret(returncode))

    def ret(self, returncode):
        rets = {0: Ret.played, -15: Ret.interrupted, 1: Ret.notfound}
        return rets.get(returncode, Ret.unknown)

    async def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None # safe/sorry?

class DQueue(asyncio.Queue):
    def putfront_nowait(self, item):
        self._queue.appendleft(item)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)

class PlayQ(Process):
    def __init__(self):
        self.q = DQueue()
        self.current = None

    async def append(self, playrun):
        await self.q.put(playrun)

    async def prepend(self, playrun):
        self.q.putfront_nowait(playrun)

    async def skip(self):
        if self.current:
            await self.current.stop()

    async def _run(self):
        async for playrun in aiter(self.q):
            try:
                log.debug('{} playing {}'.format(id(self), playrun.filename))
                self.current = playrun
                await self.current.start()
                await self.current.ended
                log.debug('{} played {}'.format(id(self), playrun.filename))
            except Exception as ex:
                log.debug(ex)

log = logging.getLogger(__name__)