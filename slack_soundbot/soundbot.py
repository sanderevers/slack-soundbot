from asyncio import CancelledError
from slacksocket import SlackSocket
from .thread import async_run_in_daemon_thread

from .config import Config
import os
import logging
import asyncio
import janus
import contextlib

class AiterQueue(asyncio.queues.Queue):
    def __aiter__(self):
        return self
    async def __anext__(self):
        return await self.get()


def list_files():
    all_files = os.listdir('./mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)

def process_events_sync(socket,jq):
    for event in socket.events():
        if event.event.get('channel')==Config.slack_channel\
                and event.event.get('type')=='message'\
                and event.event.get('user')!='soundbot':
            log.debug('received: ' + event.json)
            jq.put(event.event.get('text'))

class Player:
    def __init__(self):
        self.q = AiterQueue()
        self.task = asyncio.ensure_future(self.run())

    async def append(self, sound):
        await self.q.put(sound)

    def skip(self):
        self.task.cancel()

    async def run(self):
        while True:
            with contextlib.suppress(CancelledError):
                async for sound in self.q:
                    try:
                        log.debug('playing {}'.format(sound))
                        process = await asyncio.create_subprocess_exec(Config.play_cmd, "mp3s/{0}.mp3".format(sound))
                    except:
                        pass
                    try:
                        await process.wait()
                        log.debug("{} played".format(sound))
                    except CancelledError:
                        process.terminate()


class Bot:
    def __init__(self):
        self.socket = SlackSocket(Config.api_key, translate=True)
        self.fore = Player()
        self.back = Player()

    def run(self):
        cmdq = janus.Queue()
        asyncio.ensure_future(async_run_in_daemon_thread(process_events_sync, self.socket, cmdq.sync_q))
        asyncio.get_event_loop().run_until_complete(self.consume_cmd_q(cmdq.async_q))

    async def consume_cmd_q(self,async_q):
        while True:
            cmd = await async_q.get()
            log.debug('consuming {}'.format(cmd))
            if cmd in ('ls', 'list'):
                asyncio.ensure_future(async_run_in_daemon_thread(self.socket.send_msg,list_files(),channel_name=Config.slack_channel,confirm=False))
            elif cmd == 'stop':
                self.fore.skip()
            elif cmd == '!stop':
                self.back.skip()
            elif cmd.startswith('!'):
                await self.back.append(cmd[1:])
            else:
                await self.fore.append(cmd)

log = logging.getLogger(__name__)





