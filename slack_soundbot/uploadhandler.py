import logging
import os
import requests
from .thread import async_run_in_daemon_thread
from .process import Process


class UploadHandler(Process):
    def __init__(self, bot):
        super().__init__()
        global global_bot
        global_bot = bot

    async def _run(self):
        pass

    async def handle(self, event):
        if is_relevant_message(event):
            log.debug('received {}'.format(','.join(file.get('id') for file in event.event.get('files'))))
            file = event.event.get('files')[0]
            await Download(file).start()
            return True
        return False



class Download(Process):
    def __init__(self, file):
        super().__init__()
        self.file = file

    async def _run(self):
        await async_run_in_daemon_thread(download,self.file)
        await global_bot.send(':neu: {}'.format(self.file.get('name').split('.')[0]))


def download(file):
    url = file.get('url_private')
    filename = file.get('name')
    fileid = file.get('id')

    headers = {'Authorization': 'Bearer {}'.format(global_bot.config.api_key)}
    r = requests.get(url, headers=headers)
    full_filename = os.path.join(global_bot.config.mp3dir,filename)
    with open(full_filename,'wb') as f:
        f.write(r.content)
    log.debug('written to {}'.format(full_filename))

    delete_url = 'https://slack.com/api/files.delete'
    r = requests.post(delete_url, json={'file':fileid}, headers=headers)
    log.debug('deleted? {}'.format(r.status_code))



def is_relevant_message(event):
    return event.event.get('channel') == event.event.get('user') \
           and event.event.get('type') == 'message' \
           and event.event.get('files')




log = logging.getLogger(__name__)
