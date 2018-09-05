from slacksocket import SlackSocket
from .thread import async_run_in_daemon_thread

from .config import Config
from .process import Process, aiter
from .play import PlayQ
from .commands import handle
import logging
import asyncio
import janus
import requests
from copy import copy


def process_inq_sync(socket,syncq):
    for event in socket.events():
        syncq.put(event)
        log.debug('received: ' + event.json)

def process_outq_sync(socket,syncq):
    while True:
        event = syncq.get()
        if isinstance(event,str):
            socket.send_msg(event,channel_name=Config.slack_channel,confirm=False)
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


class Bot(Process):
    def __init__(self):
        self.socket = SlackSocket(Config.api_key, translate=True)
        self.fore = PlayQ()
        self.back = PlayQ()
        self.outq = janus.Queue()
        self.inq = janus.Queue()

    async def _run(self):
        await self.fore.start()
        await self.back.start()
        asyncio.ensure_future(async_run_in_daemon_thread(process_inq_sync, self.socket, self.inq.sync_q))
        asyncio.ensure_future(async_run_in_daemon_thread(process_outq_sync, self.socket, self.outq.sync_q))
        await self.consume_cmd_q(self.inq.async_q)

    async def send(self,event):
        # if event is a string, sends a simple message over the web socket
        # otherwise, use web api
        await self.outq.async_q.put(event)

    async def consume_cmd_q(self,async_q):
        async for ev in aiter(async_q):
            await handle(ev,self)


log = logging.getLogger(__name__)





