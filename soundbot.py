from slacksocket import SlackSocket
import subprocess
import config
import os

def handle_cmd(cmd):
    if cmd in ('ls','list'):
        s.send_msg(list_files(), channel_name=config.slack_channel)
    else:
        playsound(cmd)

def playsound(sound):
    try:
        subprocess.call([config.play_cmd,"{0}.mp3".format(sound)])
    except:
        pass

def list_files():
    all_files = os.listdir('.')
    mp3s = [parts[0] for file in all_files for parts in [file.split('.')] if parts[-1]=='mp3']
    mp3s.sort()
    return ' '.join(mp3s)

s = SlackSocket(config.api_key,translate=True)

for event in s.events():
    if event.event.get('channel')==config.slack_channel and event.event.get('type')=='message':
        print(event.json)
        handle_cmd(event.event.get('text'))
