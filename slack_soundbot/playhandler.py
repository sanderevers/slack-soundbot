import logging
import os

from .play import PlayQ, PlayRun, Ret
from .process import Process

class PlayHandler(Process):
    def __init__(self, bot):
        super().__init__()
        global global_bot
        global_bot = bot
        self.fore = PlayQ()
        self.back = PlayQ()

    async def _run(self):
        await self.fore.start()
        await self.back.start()

    async def handle(self, event):
        if is_relevant_message(event):
            log.debug('handling {}'.format(text(event)))
            cmd = self.parse(event)
            if cmd:
                await cmd.start()
                return True
        return False

    def parse(self,event):
        txt = text(event)
        if txt == 'mand':
            return Mand(self.fore)
        elif txt == '!mand':
            return Mand(self.back)
        elif txt.startswith('!'):
            return Play(txt[1:], self.back, event)
        else:
            return Play(txt, self.fore, event)

class Mand(Process):
    def __init__(self, playq):
        super().__init__()
        self.playq = playq

    async def _run(self):
        await Play('mand', self.playq, None, insert=True).start()
        await self.playq.skip()

class Play(Process):
    def __init__(self, sound, playq, event, insert=False):
        super().__init__()
        self.sound = sound
        self.playq = playq
        self.event = event
        self.insert = insert

    async def _run(self):
        filename = os.path.join(global_bot.config.mp3dir, '{}.mp3'.format(self.sound))
        playrun = PlayRun(filename)
        if self.insert:
            await self.playq.prepend(playrun)
        else:
            await self.playq.append(playrun)

        # try:
        ret = await playrun.result
        if self.event:
            await self.reply(ret)
        # except Exception as e:
        #     log.debug('Play cmd: {}'.format(e))

    async def reply(self, ret):
        emoji = \
            {Ret.played: 'white_check_mark'
                , Ret.interrupted: '-1'
                , Ret.notfound: 'x'
                , Ret.unknown: 'question'}.get(ret)
        event = \
            {'endpoint': 'reactions.add'
                , 'name': emoji
                , 'timestamp': self.event.event.get('ts')
             }
        await global_bot.send(event)


def is_relevant_message(event):
    return event.event.get('channel') == global_bot.config.slack_channel \
           and event.event.get('type') == 'message' \
           and event.event.get('user') != 'soundbot' \
           and event.event.get('text')

def text(event):
    return event.event.get('text')


log = logging.getLogger(__name__)
