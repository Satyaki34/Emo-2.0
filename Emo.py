import discord
from discord.ext import commands, tasks
import os
import sys
from dotenv import load_dotenv
from flask import Flask
import threading

# Flask web server setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is online and healthy!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Start flask web server in a separate thread
threading.Thread(target=run_flask, daemon=True).start()

# Load the token from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Comprehensive error handling
@bot.event
async def on_error(event, *args, **kwargs):
    error_type, error_value, error_traceback = sys.exc_info()
    print(f"Error in {event}: {error_type.__name__}: {error_value}")

@bot.event
async def on_command_error(ctx, error):
    print(f"Command error: {error}")
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param}")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Could not find that member.")
    else:
        await ctx.send(f"An error occurred: {error}")

# Task to keep the bot active
@tasks.loop(minutes=5)
async def status_update():
    try:
        activity = discord.Activity(type=discord.ActivityType.playing, name="!list for help")
        await bot.change_presence(activity=activity)
        print("Updated bot status")
    except Exception as e:
        print(f"Error updating status: {e}")

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    
    # Start the status update task
    status_update.start()
    
    try:
        await bot.load_extension('cogs.private_groups')
        print("Successfully loaded cogs.private_groups")
    except Exception as e:
        print(f"Failed to load cogs.private_groups: {e}")
    
    print(f"Loaded cogs: {[cog for cog in bot.cogs]}")
    try:
        await bot.load_extension('cogs.gemini_chat')
        print("Successfully loaded cogs.gemini_chat")
    except Exception as e:
        print(f"Failed to load cogs.gemini_chat: {e}")
@bot.command()
async def test(ctx):
    await ctx.send("Test command works!")

# Run the bot using the token from .env
bot.run(TOKEN)