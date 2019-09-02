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
    json.dump({"message_channel": -1},outfile, indent=4) 
    outfile.flush()
settings_file = open("settings.json")
settings = json.load(settings_file)
settings_file.close()


class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bg_task = self.loop.create_task(self.background_timer())
        self.config = self.loop.create_task(self.config_default_channel())
        
    async def config_default_channel(self):
        await self.wait_until_ready()
        
        if not self.get_channel(settings["message_channel"]): # if the channel is not assigned properly, attempt to assign it to general
            channel = discord.utils.get(self.get_all_channels(), name="general")
            if channel:
                await self.reconfig_channel(channel.id)
            else:
                print("Falling back to first channel in get_all_channels()")
                channel = self.get_all_channels[0]
                await self.reconfig_channel(channel.id)
                
    async def reconfig_channel(self, channel_id): # return True if channel is successfully changed
        try:
            channel_id = int(channel_id)
        except ValueError:
            print("Error finding channel")
            return False

        if self.get_channel(channel_id):
            channel_id = int(channel_id)
            settings_file = open("settings.json", "w")
            settings["message_channel"] = channel_id
            json.dump(settings, settings_file, indent=4)
            settings_file.close()
            return True

        else:
            print("Error finding channel")
            return False

    async def on_ready(self):
        print("Logged in as {0}".format(self.user))

    async def command_pong(self, message):
        await message.channel.send("pong")
                        
    async def command_move(self, message):
        if message.author.guild_permissions.administrator:
            msg = re.split(" ", message.content, 1)
            channel_id = msg[1][2:-1]
            await self.reconfig_channel(channel_id)
            await client.get_channel(settings["message_channel"]).send("successfully moved to this channel")
            

    async def on_message(self, message): 
        if message.author != self.user and message.channel == self.get_channel(settings["message_channel"]): # ignore messages from the bot 
            print("message from {0.author} in {0.channel}: {0.content}".format(message))
            commands={"!ping ": self.command_pong,
                      "!move ": self.command_move}
            for key in commands:
                print(key)
                if message.content.startswith(key) or message.content == key[:-1]: # check if message starts with command
                    await commands[key](message)

    async def on_time(self):
        if self.get_channel(settings["message_channel"]):
            channel = self.get_channel(settings["message_channel"])
            await channel.send("sample text")
        else:
            print("invalid configuration for automatic messages")
            
    async def background_timer(self):
        await self.wait_until_ready()
        
        channel = self.get_channel(settings["message_channel"])
        while not self.is_closed():
            current_time = time.asctime()
            day_of_week = current_time[:3] # Sun, Mon, Tue, Wed, Thu, Fri, Sat
            month = current_time[4:7]      # Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
            day = current_time[8:10]       # space padded 2 character number
            hour = current_time[11:13]     # 0 padded 2 character number
            minute = current_time[14:16]   # 0 padded 2 character number
            second = current_time[17:19]   # 0 padded 2 character number
            year = current_time[20:]       # 4 character number
            
            # example reminder for 09:00 MWF class
            days = ["Mon", "Wed", "Fri"]
            if day_of_week in days and hour == "09" and minute == "00" and second == "00":
                await channel.send("Reminder")
            await asyncio.sleep(1)

client = DiscordBot()
client.run(clientdict["token"])
