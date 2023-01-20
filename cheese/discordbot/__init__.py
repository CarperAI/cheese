import discord
import os
from dotenv import load_dotenv
import random

from cheese.api import CHEESEAPI

def get_consts():
    """
        Check for a file called cheesebot.txt in run directory
        Read lines in order as token, server_id, admin_id
        token is token for bot
        server_id is id of server bot will be operating in
        admin_id is id for role that will be able to use admin commands
        user_file is path of file to store user names to
    """
    with open('cheesebot.txt', 'r') as f:
        token = f.readline().strip()
        server_id = int(f.readline().strip())
        admin_id = int(f.readline().strip())
        user_file = f.readline().strip()
    return token, server_id, admin_id, user_file

def get_file_as_dict(path):
    """
        Read a file as a dictionary
        Each line should be of the form key:value
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    d = {}
    for line in lines:
        key, value = line.split(':')
        d[key] = value
    return d

TOKEN, SERVER_ID, ADMIN_ID, USER_FILE_PATH = get_consts()

client = discord.Client()
api = CHEESEAPI()
active_msg = None

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    # Only respond to messages in server_id
    if message.guild.id != SERVER_ID:
        return
    # Only respond to messages from admin_id role
    if not any([role.id == ADMIN_ID for role in message.author.roles]):
        return
    # only respond to messages that start with '!cheese'
    if not message.content.startswith('!cheese'):
        return

    if message.content == "!cheese ping":
        await message.channel.send("pong")
    
    if message.content == "!cheese launch":
        url = api.launch()

    if message.content == "!cheese stats":
        stats = api.get_stats()
        n_clients = stats['num_clients']
        n_tasks = stats['num_tasks']
        await message.channel.send(f"CHEESE experiment is currently running with {n_clients} clients, who have collectively labelled {n_tasks} examples.")
    if message.content == "!cheese getusers":
        new_msg = await message.channel.send(f"Collecting users for CHEESE experiment! Please react to this message with a cheese emoji to be sent login information.")
        # React to the message we just sent 
        await new_msg.add_reaction('🧀')
        active_msg = new_msg

# For reacts

@client.event
async def on_reaction_add(reaction, user):
    url = api.get_stats()["url"]
    if reaction.message.id == active_msg.id:
        # Check if this user has already been added
        if user.id in get_file_as_dict(USER_FILE_PATH):
            await user.send(f"You have already been added to the CHEESE experiment! Your id is {get_file_as_dict(USER_FILE_PATH)[user.id]}. You can login at {url}")

            return
        # Make a random 8 digit number as id
        cheese_id = random.randint(10000000, 99999999)
        # Append to file
        with open(USER_FILE_PATH, 'a') as f:
            f.write(f"{user.id}:{cheese_id}")
        f.close()
        
        # Send a DM to the user who reacted with some login info and append it to file
        
        await user.send(f"Here is your login ID for the CHEESE experiment: {cheese_id}. Join at {url}.")

client.run(TOKEN)