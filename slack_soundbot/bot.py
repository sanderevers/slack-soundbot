from slacksocket import SlackSocket
from .thread import async_run_in_daemon_thread

from .process import Process, aiter
import logging
import asyncio
import janus
import requests
from copy import copy




class Bot(Process):
    def __init__(self, config, handlerclasses):
        super().__init__()
        self.config = config
        self.socket = SlackSocket(self.config.api_key)
        self.outq = janus.Queue()
        self.inq = janus.Queue()
        self.handlers = [cls(self) for cls in handlerclasses]


    async def _run(self):
        asyncio.ensure_future(async_run_in_daemon_thread(self.process_inq_sync, self.socket, self.inq.sync_q))
        asyncio.ensure_future(async_run_in_daemon_thread(self.process_outq_sync, self.socket, self.outq.sync_q))
        for handler in self.handlers:
            await handler.start()
        await self.consume_cmd_q(self.inq.async_q)

    async def send(self,event):
        # if event is a string, sends a simple message over the web socket
        # otherwise, use web api
        await self.outq.async_q.put(event)

    async def consume_cmd_q(self,async_q):
        async for ev in aiter(async_q):
            for handler in self.handlers:
                if await handler.handle(ev):
                    break

    def process_inq_sync(self, socket, syncq):
        for event in socket.events():
            syncq.put(event)
            log.debug('received: ' + event.json)

    def process_outq_sync(self, socket, syncq):
        while True:
            event = syncq.get()
            if isinstance(event, str):
                socket.send_msg(event, channel_name=self.config.slack_channel, confirm=False)
            else:
                channel_id = socket._lookup_channel_by_name(self.config.slack_channel)['channel_id']
                slack_event = copy(event)
                slack_event['channel'] = channel_id
                del slack_event['endpoint']
                url = 'https://slack.com/api/{}'.format(event['endpoint'])
                headers = {'Authorization': 'Bearer {}'.format(self.config.api_key)}
                r = requests.post(url, json=slack_event, headers=headers)
                log.debug('web api returned {}'.format(r.status_code))
                log.debug(r.text)


log = logging.getLogger(__name__)





