import json
import asyncio
import discord
import time
import re

# start out by grabbing client info
clientinfo = open("clientinfo.json")
clientdict = json.load(clientinfo)

# settings file
try:
    open("settings.json", "r")
except FileNotFoundError:
    print("building settings.json")
    outfile = open("settings.json", "w")
    json.dump({"message_channel": "message", },outfile, indent=4) 
    outfile.flush()
settings_file = open("settings.json")
settings = json.load(settings_file)
settings_file.close()


class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bg_task = self.loop.create_task(self.background_timer())


    async def on_ready(self):
        print("Logged in as {0}".format(self.user))

    async def command_pong(self, message):
        await message.channel.send("pong")
                        
    async def command_move(self, message):
        settings_file = open("settings.json", "w")
        try:
            msg = re.split(" ", message.content, 1)
            settings["message_channel"] = int(msg[1][2:-1])
            json.dump(settings, settings_file, indent=4)
            await client.get_channel(settings["message_channel"]).send("successfully moved to this channel")
            settings_file.close()
        except ValueError:
            await message.channel.send("invalid channel")

    async def on_message(self, message):
        print("message from {0.author} in {0.channel}: {0.content}".format(message))
        commands={"!ping": self.command_pong,
                  "!move": self.command_move}
        for key in commands:
            print(key)
            if message.content.startswith(key): # check if message starts with command
                await commands[key](message)

    async def on_time(self):
        if type(settings["message_channel"]) != type(int(1)): # check if the message channel is a valid integer
            print("invalid configuration for automatic messages")
        else:
            channel = self.get_channel(settings["message_channel"])
            await channel.send("sample text")

    async def background_timer(self):
        await self.wait_until_ready()
        
        channel = self.get_channel(settings["message_channel"])
        while not self.is_closed():
            current_time = time.asctime()
            day_of_week = current_time[:3]
            month = current_time[4:7]
            day = current_time[8:10]
            hour = current_time[11:13]
            minute = current_time[14:16]
            second = current_time[17:19]
            year = current_time[20:]
            
            # example reminder for 09:00 MWF class
            days = ["Mon", "Wed", "Fri"]
            if day_of_week in days and hour == "09" and minute == "00" and second == "00":
                print("attempting to send reminder")
                await channel.send("Reminder")


            print(current_time)
            await asyncio.sleep(1)


client = DiscordBot()
client.run(clientdict["token"])
