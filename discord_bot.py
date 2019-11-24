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
    json.dump({"!ping": {"channel": -1, "return_type": "message", "data": "pong", "indexed": False, "admin": False}}, outfile, indent=4)
    outfile.flush()
    outfile.close()
commands_file = open("commands.json")
commands = json.load(commands_file)
commands_file.close()

class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    async def on_ready(self):
        print("Logged in as {0}".format(self.user))
    
    async def config_default_channel(self):
        await self.wait_until_ready()

        if not self.get_channel(settings["message_channel"]["default"]): # attempt to assign channel if default is invalid.            
            channel = discord.utils.get(self.get_all_channels(), name="general") # default to general, fallback on first channel
            if channel:
                await self.reconfig_channel(channel.id)
            else:
                print("General not found, falling back to first detected channel")
                channel = await self.get_all_channels()
                channel = next(channel)
                await self.reconfig_channel(channel.id)
                
    async def reconfig_channel(self, channel_id, category="message_channel", channel_in="default"): # RETURN True if channel
                                                                                                    # is successfully updated
        try:
            channel_id = int(channel_id)
        except ValueError:
            return False
        
        if self.get_channel(channel_id):
            channel_id = int(channel_id)
            settings_file = open("settings.json", "w")
            settings[category][channel_in] = channel_id
            json.dump(settings, settings_file, indent=4)
            return True
        else:
            return False
        
    ######################################################
    # Functions for handling commands from commands.json #
    ######################################################
    
    # from_file refers to the file that is being fetched
    async def command_simple_message(self, key, message, from_file=""): # command for sending a "message"
        if ((message.author.guild_permissions.administrator)
             or (not message.author.guild_permissions.administrator and not commands[key]["admin"])): # permissions for basic users and admin
            data = commands[key]["data"]
            if from_file:
                data = from_file
            await client.get_channel(commands[key]["channel"]).send(data)
    
    async def command_upload_file(self, key, message, from_file=""): # command for sending a "file"
        if ((message.author.guild_permissions.administrator)
             or (not message.author.guild_permissions.administrator and not commands[key]["admin"])):
            data = commands[key]["data"]
            if from_file:
                data = from_file
            fp = open(data, "rb")
            await client.get_channel(commands[key]["channel"]).send(file=discord.File(fp))
            fp.close()
            
    ######################
    # Built in functions #
    ######################
    
    # add commands to commands.json (text only)
    async def command_add_command(self, message):
        if message == "!addcom":
            await message.channel.send("invalid syntax!")
            return False
        else:
            content = message.content[len("!addcom "):]
            content = re.split(" ", content, maxsplit=1) # split into a list at the first space
            commands[content[0]] = {"channel": message.channel.id, "return_type": "message", "data": content[1], "indexed": False,
                                    "admin": False}
            fp = open("commands.json", "w")
            json.dump(commands, fp, sort_keys=True, indent=4)
            fp.flush()
            fp.close()
            await message.channel.send("Successfully added command `{}` with content `{}`".format(content[0], content[1]))
            
    
    ######################
    # Message Processing #
    ######################
    
    async def on_message(self, message): # returns true if the command is processed
        if message.author != self.user: # ignore messages from self
            print("message from {0.author} in {0.channel}: {0.content}".format(message))
            built_in_commands = {"!addcom": self.command_add_command}
            
            # process built in commands
            for key in built_in_commands:
                if message.content.startswith(key + " ") or message.content == key:
                    await built_in_commands[key](message)
                    return True
            # process commands.json commands
            for key in commands:
                if message.content.startswith(key + " ") or message.content == key:
                    if commands[key]["return_type"] == "message":
                        await self.command_simple_message(key, message)
                    elif commands[key]["return_type"] == "file":
                        await self.command_upload_file(key, message)
                        
                    """ TODO Figure out how to implement this.
                    elif commands[key]["return_type"] == "message_from_file":
                        await self.command_simple_message(key, message, )
                    elif commands[key]["return_type"] == "file_from_file":
                        await self.command_from_file(key, message, "file")
                    """
                    
    
client = DiscordBot()
client.run(clientdict["token"])
