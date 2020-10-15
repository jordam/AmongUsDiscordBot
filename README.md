# AmongUsDiscordBot
Among Us Kill / Exile aware voice channel bot. Mute / move dead players to dead voice chat

Includes AmongUsParser from https://github.com/jordam/amongUsParser

Built with python 3.6 64 bit windows

Requires pcap on system for packet reading

Requires python libraries: scapy, janus, discord

Shoutouts to https://github.com/denverquane/amongusdiscord for a lot of the inspiration for the project.

To Use
======
Follow the instructions at https://realpython.com/how-to-make-a-discord-bot-python/ to create a discord bot and add it to your guild.

Edit discord-bot.py to add in the following at the top

* Your bot token
* Your guild name
* A voice channel to send living users
* A voice channel to send dead users

Start discord-bot.py. Pick the device you get internet via from the list shown. You should see confirmation that the bot is connected and registered your alive and dead channels correctly. 

You should see the message "Ready to join games!" once everything is ready for you to play Among Us. Now you can join a game. Once you have entered a lobby you should see "Joined Game!" indicating the system is properly detecting game data.

Set your in game username to your discord username. Some characters will not enter in game and the in game name can only be 10 characters long. This should be ok, skip any characters you can not enter and stop if the name grows to large.
