import os

class ListHandler: #Process?

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def start(self):
        pass

    async def handle(self, event):
        if event.event.get('channel') == self.bot.config.slack_channel \
                and event.event.get('type') == 'message' \
                and event.event.get('user') != 'soundbot'\
                and event.event.get('text') in ('ls','list'):
            await self.bot.send(list_files(self.bot.config.mp3dir))
            return True


def list_files(mp3dir):
    all_files = os.listdir(mp3dir)
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)

