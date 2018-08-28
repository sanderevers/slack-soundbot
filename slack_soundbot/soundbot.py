from asyncio import CancelledError, Queue
from slacksocket import SlackSocket
from .thread import async_run_in_daemon_thread

from .config import Config
import os
import logging
import asyncio
import janus
import contextlib

class DQueue(Queue):
    def putfront_nowait(self, item):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        if self.full():
            raise QueueFull
        self._queue.appendleft(item)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)

async def aiter(queue):
    while True:
        yield await queue.get()

def list_files():
    all_files = os.listdir('./mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)

def process_events_sync(socket,jq):
    for event in socket.events():
        jq.put(event)
        log.debug('received: ' + event.json)


def is_relevant_message(event):
    return event.event.get('channel')==Config.slack_channel\
            and event.event.get('type')=='message'\
            and event.event.get('user')!='soundbot'

def text(event):
    return event.event.get('text')

class PlayRun:
    def __init__(self, filename):
        self.process = None
        self.filename = filename

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(Config.play_cmd, self.filename)
        asyncio.ensure_future(self.wait())

    async def wait(self):
        if self.process:
            ret = await self.process.wait()
            self.process = None
            log.debug('wait ended in {}'.format(ret))
            return ret

    async def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None


class PlayQ:
    def __init__(self):
        self.q = DQueue()
        self.playrun = PlayRun(None)
        asyncio.ensure_future(self.run())

    async def append(self, sound):
        await self.q.put(sound)

    async def prepend(self, sound):
        self.q.putfront_nowait(sound)

    async def skip(self):
        await self.playrun.stop()

    async def run(self):
        async for sound in aiter(self.q):
            try:
                log.debug('playing {}'.format(sound))
                self.playrun = PlayRun("mp3s/{0}.mp3".format(sound))
                await self.playrun.start()
                await self.playrun.wait()
                log.debug("{} played".format(sound))
            except:
                pass


class Bot:
    def __init__(self):
        self.socket = SlackSocket(Config.api_key, translate=True)
        self.fore = PlayQ()
        self.back = PlayQ()

    def run(self):
        cmdq = janus.Queue()
        asyncio.ensure_future(async_run_in_daemon_thread(process_events_sync, self.socket, cmdq.sync_q))
        asyncio.get_event_loop().run_until_complete(self.consume_cmd_q(cmdq.async_q))

    async def consume_cmd_q(self,async_q):
        async for cmd in (text(ev) async for ev in aiter(async_q) if is_relevant_message(ev)):
            log.debug('consuming {}'.format(cmd))
            if cmd in ('ls', 'list'):
                asyncio.ensure_future(async_run_in_daemon_thread(self.socket.send_msg,list_files(),channel_name=Config.slack_channel,confirm=False))
            elif cmd == 'mand':
                await self.fore.prepend('mand')
                await self.fore.skip()
            elif cmd == '!mand':
                await self.back.prepend('mand')
                await self.back.skip()
            elif cmd.startswith('!'):
                await self.back.append(cmd[1:])
            else:
                await self.fore.append(cmd)

log = logging.getLogger(__name__)





