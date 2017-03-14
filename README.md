## Slack soundbot

1. create a bot for your organisation using the Slack web interface
2. create a channel for your bot to listen to and invite your bot there
3. copy `config.py.example` to `config.py`
4. fill in your bot's API key and channel name in `config.py`
5. install a command line mp3 file player, e.g. `mplayer`. On MacOS you can use `afplay`
6. `pip install slacksocket`
7. `python soundbot.py`
8. put some mp3 files in this directory
9. enter a filename (leave off .mp3) in your Slack channel
10. or say "list" to list the available mp3s
11. enjoy!
