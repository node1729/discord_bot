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
    json.dump({"message_channel": {"default": -1}, "commands": {}},outfile, indent=4) 
    outfile.flush()
    outfile.close()
settings_file = open("settings.json")
settings = json.load(settings_file)
settings_file.close()

# commands file
try:
    open("commands.json")
except FileNotFoundError:
    print("building commands.json")
    outfile = open("commands.json", "w")
    json.dump({"!ping": {"channel": -1, "return_type": "message", "data": "pong", "indexed": False, "users": "any"}}, outfile, indent=4)
    outfile.flush()
    outfile.close()
commands_file = open("commands.json")
commands = json.load(commands_file)
commands_file.close()

class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bg_task = self.loop.create_task(self.background_timer())
        self.config = self.loop.create_task(self.config_default_channel())
        
    async def config_default_channel(self):
        await self.wait_until_ready()
        
        if not self.get_channel(settings["message_channel"]["default"]): # if the channel is not assigned properly,
                                                                         # attempt to assign it to general
            channel = discord.utils.get(self.get_all_channels(), name="general")
            if channel:
                await self.reconfig_channel(channel.id)
            else:
                print("Falling back to first channel in get_all_channels()")
                channel = await self.get_all_channels()
                channel = next(channel)
                await self.reconfig_channel(channel.id)
        
    async def reconfig_channel(self, channel_id, category="message_channel", channel_in="default"): # return True if channel 
                                                                                                    # is successfully changed
        try:
            channel_id = int(channel_id)
        except ValueError:
            print("Error finding channel")
            return False

        if self.get_channel(channel_id):
            channel_id = int(channel_id)
            settings_file = open("settings.json", "w")
            settings[category][channel_in] = channel_id
            json.dump(settings, settings_file, indent=4)
            settings_file.close()
            return True

        else:
            print("Error finding channel")
            return False

    async def on_ready(self):
        print("Logged in as {0}".format(self.user))

    """async def command_pong(self, message):
            await message.channel.send("pong")"""
                        
    async def command_move(self, message, channel_in="default"):
        if message.author.guild_permissions.administrator:
            msg = re.split(" ", message.content, 2)
            if len(msg) == 2: # move entire bot to a channel
                channel_id = msg[1][2:-1]
                await self.reconfig_channel(channel_id)
                for key in settings["commands"]:
                    await self.reconfig_channel(channel_id, "commands", key)
                await client.get_channel(settings["message_channel"][channel_in]).send("successfully moved to this channel")            
                
            elif len(msg) == 3: # move a single command to a channel
                channel_id = msg[2][2:-1]
                command_move = msg[1]
                await self.reconfig_channel(channel_id, category="commands", channel_in=command_move)
    
    #########################################################
    # begin Functions to handle commands from commands.json # 
    #########################################################
    
    async def command_simple_message(self, key, message, from_file=""): # command for sending a "message" from the commands.json file
        if ((message.author.guild_permissions.administrator)
             or (not message.author.guild_permissions.administrator and not commands[key]["admin"])):
            data = commands[key]["data"]
            if from_file:
                data = from_file
            await client.get_channel(commands[key]["channel"]).send(data)
    
    async def command_upload_file(self, key, message, from_file=""): # command for sending a "file" from the commands.json file
        if ((message.author.guild_permissions.administrator)
            or (not message.author.guild_permissions.administrator and not commands[key]["admin"])):
            data = commands[key]["data"]
            if from_file:
                data = from_file
            fp = open(data, "rb")
            await client.get_channel(commands[key]["channel"]).send(file=discord.File(fp))
            fp.close()
            
#    async def command_add_command(self, key, message):
        
        
    #######################################################
    # end Functions to handle commands from commands.json #
    #######################################################
    
    async def on_message(self, message): # returns true if command is processed
        if message.author != self.user: # ignore messages from the bot 
            print("message from {0.author} in {0.channel}: {0.content}".format(message))
            built_in_commands = {
                                 #"!move": self.command_move
                                 }
            for key in built_in_commands:
                if message.content.startswith(key + " ") or message.content == key:
                    await built_in_commands[key](message)
                    return True

            for key in commands:
                if message.content.startswith(key + " ") or message.content == key:
                    if commands[key]["return_type"] == "message":
                        await self.command_simple_message(key, message)
                    elif commands[key]["return_type"] == "file":
                        await self.command_upload_file(key, message)
                    elif commands[key]["return_type"] == "message_from_file":
                        await self.command_from_file(key, message, "message")
                    elif commands[key]["return_type"] == "file_from_file":
                        await self.command_from_file(key, message, "file")
            
                        
    async def on_time(self):
        if self.get_channel(settings["message_channel"]["default"]):
            channel = self.get_channel(settings["message_channel"]["default"])
            await channel.send("sample text")
        else:
            print("invalid configuration for automatic messages")
            
    async def background_timer(self):
        await self.wait_until_ready()
        
        channel = self.get_channel(settings["message_channel"]["default"])
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
