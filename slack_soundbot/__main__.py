import os
import sys
import logging
import yaml
import asyncio
import warnings

from .bot import Bot
from .config import Config

def read_config(filename):
    with open(filename) as f:
        yml = yaml.safe_load(f)
    for key,val in yml.items():
        if hasattr(Config,key):
            setattr(Config,key,val)
        else:
            logging.warning('Unknown configuration key "{}"'.format(key))

def main():
    default_config_file = os.path.join(os.path.expanduser('~'), '.slack-soundbot.conf')
    if len(sys.argv)>1:
        read_config(sys.argv[1])
    elif os.path.exists(default_config_file):
        read_config(default_config_file)

    if Config.debug:
        logging.basicConfig(level=logging.DEBUG)
        asyncio.get_event_loop().set_debug(True)
        warnings.simplefilter("always", ResourceWarning)

    asyncio.get_event_loop().run_until_complete(Bot()._run())

log = logging.getLogger(__package__)
if __name__=='__main__':
    main()
