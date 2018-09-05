from .process import Process
from .play import PlayRun, Ret
from .config import Config
import logging
import os

async def handle(event,bot):
    if is_relevant_message(event):
        log.debug('handling {}'.format(text(event)))
        cmd = parse(event,bot)
        if cmd:
            await cmd.start()

def is_relevant_message(event):
    return event.event.get('channel')==Config.slack_channel\
            and event.event.get('type')=='message'\
            and event.event.get('user')!='soundbot'\
            and event.event.get('text')

def text(event):
    return event.event.get('text')

def parse(event,bot):
    txt = text(event)
    if txt in ('ls', 'list'):
        return List(bot)
    elif txt == 'mand':
        return Mand(bot.fore)
    elif txt == '!mand':
        return Mand(bot.back)
    elif txt.startswith('!'):
        return Play(txt[1:], bot.back, event, bot)
    else:
        return Play(txt, bot.fore, event, bot)

def list_files():
    all_files = os.listdir('./mp3s')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)

class List(Process):
    def __init__(self,bot):
        self.bot = bot

    async def _run(self):
        await self.bot.send(list_files())

class Mand(Process):
    def __init__(self, playq):
        self.playq = playq

    async def _run(self):
        await Play('mand', self.playq, None, None, insert=True).start()
        await self.playq.skip()

class Play(Process):
    def __init__(self, sound, playq, event, bot, insert=False):
        self.sound = sound
        self.playq = playq
        self.event = event
        self.bot = bot
        self.insert = insert

    async def _run(self):
        playrun = PlayRun("mp3s/{}.mp3".format(self.sound))
        if self.insert:
            await self.playq.prepend(playrun)
        else:
            await self.playq.append(playrun)

        ret = await playrun.ended

        if self.event:
            await self.reply(ret)

    async def reply(self, ret):
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

log = logging.getLogger(__name__)