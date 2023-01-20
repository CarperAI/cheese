import discord
import os
from dotenv import load_dotenv
import random

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

TOKEN, SERVER_ID, ADMIN_ID, USER_FILE_PATH = get_consts()

client = discord.Client()
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
    
    if message.content == "!cheese getusers":
        new_msg = await message.channel.send(f"Collecting users for CHEESE experiment! Please react to this message with a cheese emoji to be sent login information.")
        # React to the message we just sent 
        await new_msg.add_reaction('🧀')
        active_msg = new_msg

# For reacts

@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.id == active_msg.id:
        # Make a random 8 digit number as id
        cheese_id = random.randint(10000000, 99999999)
        # Append to file
        with open(USER_FILE_PATH, 'a') as f:
            f.write(f"{user.id}:{cheese_id}")
        f.close()
        
        # Send a DM to the user who reacted with some login info and append it to file
        
        await user.send(f"Here is your login ID for the CHEESE experiment: {cheese_id}")

client.run(TOKEN)