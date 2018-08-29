from asyncio import CancelledError, Queue, Future
from slacksocket import SlackSocket
from .thread import async_run_in_daemon_thread

from .config import Config
import os
import logging
import asyncio
import janus
import json
import requests
from copy import copy

class DQueue(Queue):
    def putfront_nowait(self, item):
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

def is_relevant_message(event):
    return event.event.get('channel')==Config.slack_channel\
            and event.event.get('type')=='message'\
            and event.event.get('user')!='soundbot'\
            and event.event.get('text')

def text(event):
    return event.event.get('text')

class Ret:
    played = object()
    interrupted = object()
    notfound = object()
    unknown = object()

class PlayRun:
    def __init__(self, filename, outcome):
        self.process = None
        self.filename = filename
        self.outcome = outcome

    async def start(self):
        asyncio.ensure_future(self._run())

    async def _run(self):
        self.process = await asyncio.create_subprocess_exec(Config.play_cmd, self.filename)
        returncode = await self.process.wait()
        log.debug('PlayRun {} ended in {}'.format(self.filename, returncode))
        self.outcome.set_result(self.ret(returncode))
        self.process = None

    async def wait(self):
        if self.process:
            await self.process.wait()

    def ret(self, returncode):
        rets = {0: Ret.played, -15: Ret.interrupted, 1: Ret.notfound}
        return rets.get(returncode, Ret.unknown)

    async def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None # safe/sorry?


class PlayQ:
    def __init__(self):
        self.q = DQueue()
        self.playrun = None
        asyncio.ensure_future(self.run())

    async def append(self, cmd):
        await self.q.put(cmd)

    async def prepend(self, cmd):
        self.q.putfront_nowait(cmd)

    async def skip(self):
        if self.playrun:
            await self.playrun.stop()

    async def run(self):
        async for cmd in aiter(self.q):
            try:
                sound = cmd.sound
                log.debug('playing {}'.format(sound))
                self.playrun = PlayRun("mp3s/{0}.mp3".format(sound),cmd.outcome)
                await self.playrun.start()
                await self.playrun.wait()
                log.debug("{} played".format(sound))
            except:
                pass

class Command:
    def __init__(self, sound, event, bot):
        self.outcome = Future()
        self.event = event
        self.bot = bot
        self.sound = sound
        asyncio.ensure_future(self.respond())

    async def respond(self):
        ret = await self.outcome
        emoji =\
            { Ret.played: 'white_check_mark'
            , Ret.interrupted: '-1'
            , Ret.notfound: 'x'
            , Ret.unknown: 'question' }.get(ret)
        event =\
            { 'endpoint': 'reactions.add'
            , 'name': emoji
            , 'timestamp': self.event.event.get('ts')
            }
        await self.bot.send(event)


def process_inq_sync(socket,syncq):
    for event in socket.events():
        syncq.put(event)
        log.debug('received: ' + event.json)

def process_outq_sync(socket,syncq):
    while True:
        event = syncq.get()
        if isinstance(event,str):
            socket.send_msg(str,channel_name=Config.slack_channel,confirm=False)
        else:
            channel_id=socket._lookup_channel_by_name(Config.slack_channel)['channel_id']
            slack_event = copy(event)
            slack_event['channel'] = channel_id
            del slack_event['endpoint']
            url = 'https://slack.com/api/{}'.format(event['endpoint'])
            headers = {'Authorization': 'Bearer {}'.format(Config.api_key)}
            r = requests.post(url,json=slack_event,headers=headers)
            log.debug('web api returned {}'.format(r.status_code))
            log.debug(r.text)


class Bot:
    def __init__(self):
        self.socket = SlackSocket(Config.api_key, translate=True)
        self.fore = PlayQ()
        self.back = PlayQ()

    def run(self):
        inq = janus.Queue()
        self.outq = janus.Queue()
        asyncio.ensure_future(async_run_in_daemon_thread(process_inq_sync, self.socket, inq.sync_q))
        asyncio.ensure_future(async_run_in_daemon_thread(process_outq_sync, self.socket, self.outq.sync_q))
        asyncio.get_event_loop().run_until_complete(self.consume_cmd_q(inq.async_q))

    async def send(self,event):
        # if event is a string, sends a simple message over the web socket
        # otherwise, use web api
        await self.outq.async_q.put(event)


    async def consume_cmd_q(self,async_q):
        async for ev in aiter(async_q):
            if is_relevant_message(ev):
                cmd = text(ev)
                log.debug('consuming {}'.format(cmd))
                if cmd in ('ls', 'list'):
                    asyncio.ensure_future(async_run_in_daemon_thread(self.socket.send_msg,list_files(),channel_name=Config.slack_channel,confirm=False))
                elif cmd == 'mand':
                    await self.fore.prepend(Command('mand',ev,self))
                    await self.fore.skip()
                elif cmd == '!mand':
                    await self.back.prepend(Command('mand',ev,self))
                    await self.back.skip()
                elif cmd.startswith('!'):
                    await self.back.append(Command(cmd[1:],ev,self))
                else:
                    await self.fore.append(Command(cmd,ev,self))

log = logging.getLogger(__name__)





