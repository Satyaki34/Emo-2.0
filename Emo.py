import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
# Add this near the top of your file
import threading
import http.server
import socketserver

# Add this function
def run_web_server():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Web server running on port {PORT}")
        httpd.serve_forever()

# Add this before your bot starts
threading.Thread(target=run_web_server, daemon=True).start()

# Load the token from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        await bot.load_extension('cogs.private_groups')
        print("Successfully loaded cogs.private_groups")
    except Exception as e:
        print(f"Failed to load cogs.private_groups: {e}")
    
    print(f"Loaded cogs: {[cog for cog in bot.cogs]}")

@bot.command()
async def test(ctx):
    await ctx.send("Test command works!")

# Run the bot using the token from .env
bot.run(TOKEN)