import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
import os
from dotenv import load_dotenv

class DnDGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Load environment variables
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')
        
        # Initialize MongoDB or fallback to in-memory storage
        if not mongo_uri:
            print("WARNING: MONGO_URI not found in .env file!")
            print("DnD games will be stored in memory and lost on restart.")
            self.use_mongo = False
            self.active_games = {}  # Stores active games by channel ID
        else:
            # Initialize MongoDB connection
            try:
                self.mongo_client = MongoClient(mongo_uri)
                self.db = self.mongo_client['emo_bot']
                self.games_collection = self.db['dnd_games']
                
                # Create indexes for faster queries
                self.games_collection.create_index("channel_id", unique=True)
                
                self.use_mongo = True
                print("Successfully connected to MongoDB for DnD games")
            except Exception as e:
                print(f"Failed to connect to MongoDB for DnD games: {e}")
                print("DnD games will be stored in memory and lost on restart.")
                self.use_mongo = False
                self.active_games = {}
    
    async def get_game(self, channel_id):
        """Get an active game from storage"""
        if not self.use_mongo:
            return self.active_games.get(str(channel_id))
        else:
            game = self.games_collection.find_one({"channel_id": str(channel_id)})
            return game
    
    async def save_game(self, channel_id, game_data):
        """Save game data to storage"""
        if not self.use_mongo:
            self.active_games[str(channel_id)] = game_data
        else:
            # Upsert - update if exists, insert if not
            self.games_collection.update_one(
                {"channel_id": str(channel_id)},
                {"$set": game_data},
                upsert=True
            )
    
    async def delete_game(self, channel_id):
        """Delete a game from storage"""
        if not self.use_mongo:
            if str(channel_id) in self.active_games:
                del self.active_games[str(channel_id)]
        else:
            self.games_collection.delete_one({"channel_id": str(channel_id)})
    
    @commands.command(name="dnd")
    async def dnd_setup(self, ctx):
        """Setup a new Dungeons & Dragons game session
        
        Example: !dnd
        """
        channel_id = str(ctx.channel.id)
        
        # Check if there's already a game in this channel
        existing_game = await self.get_game(channel_id)
        if existing_game:
            await ctx.send("A D&D game is already set up in this channel.")
            return
        
        # Create embed for game setup
        embed = discord.Embed(
            title="🎲 D&D Game Setup 🐉",
            description="Let's set up your Dungeons & Dragons game!",
            color=discord.Color.dark_purple()
        )
        
        await ctx.send(embed=embed)
        
        # Ask for players
        await ctx.send("**Step 1:** Please tag all players who will participate (including yourself if you're playing)")
        
        def check_message(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            # Get players
            player_msg = await self.bot.wait_for('message', check=check_message, timeout=60)
            mentioned_players = player_msg.mentions
            
            if not mentioned_players:
                await ctx.send("No players were mentioned. Game setup cancelled.")
                return
            
            player_names = [player.display_name for player in mentioned_players]
            player_ids = [str(player.id) for player in mentioned_players]
            
            # Ask about Game Master
            gm_embed = discord.Embed(
                title="Game Master Selection",
                description="Who will be the Game Master (DM)?",
                color=discord.Color.dark_purple()
            )
            
            # Add Emo as option
            options = "**0.** Emo (AI Game Master)\n"
            
            # Add players as options
            for i, player in enumerate(player_names, 1):
                options += f"**{i}.** {player}\n"
            
            gm_embed.add_field(name="Options", value=options)
            await ctx.send(embed=gm_embed)
            await ctx.send("Enter the number of your choice:")
            
            # Get GM choice
            gm_choice_msg = await self.bot.wait_for('message', check=check_message, timeout=60)
            
            try:
                choice = int(gm_choice_msg.content.strip())
                if choice < 0 or choice > len(player_names):
                    await ctx.send("Invalid choice. Game setup cancelled.")
                    return
                
                # Process the choice
                if choice == 0:
                    gm_name = "Emo"
                    gm_id = str(self.bot.user.id)
                    is_ai_gm = True
                else:
                    gm_name = player_names[choice-1]
                    gm_id = player_ids[choice-1]
                    is_ai_gm = False
                
                # Create success embed
                success_embed = discord.Embed(
                    title="🎲 D&D Game Created! 🐉",
                    description="Your game has been set up successfully!",
                    color=discord.Color.green()
                )
                
                player_list = ", ".join(player_names)
                success_embed.add_field(name="Players", value=player_list)
                success_embed.add_field(name="Game Master", value=gm_name)
                
                # Store the game data
                game_data = {
                    "channel_id": channel_id,
                    "created_by": str(ctx.author.id),
                    "created_at": ctx.message.created_at.isoformat(),
                    "players": player_names,
                    "player_ids": player_ids,
                    "game_master": gm_name,
                    "game_master_id": gm_id,
                    "is_ai_gm": is_ai_gm,
                    "state": "setup",
                    "last_updated": ctx.message.created_at.isoformat()
                }
                
                await self.save_game(channel_id, game_data)
                
                await ctx.send(embed=success_embed)
                
                # Final message based on GM type
                if is_ai_gm:
                    await ctx.send("Emo will be your Game Master! More D&D commands will be available in future updates.")
                else:
                    await ctx.send(f"{gm_name} will be your Game Master! More D&D commands will be available in future updates.")
                
            except ValueError:
                await ctx.send("Please enter a valid number. Game setup cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("Setup timed out. Please try again when you're ready.")
    
    @commands.command(name="dnd_status")
    async def dnd_status(self, ctx):
        """Show the status of the current D&D game in this channel"""
        channel_id = str(ctx.channel.id)
        game = await self.get_game(channel_id)
        
        if not game:
            await ctx.send("There is no active D&D game in this channel. Use `!dnd` to create one.")
            return
        
        # Create status embed
        embed = discord.Embed(
            title="🎲 D&D Game Status 🐉",
            description="Current game information:",
            color=discord.Color.blue()
        )
        
        # Add game details
        embed.add_field(name="Game Master", value=game["game_master"], inline=True)
        embed.add_field(name="Players", value=", ".join(game["players"]), inline=False)
        embed.add_field(name="State", value=game["state"].capitalize(), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="end_dnd")
    async def end_dnd(self, ctx):
        """End the current D&D game in this channel"""
        channel_id = str(ctx.channel.id)
        game = await self.get_game(channel_id)
        
        if not game:
            await ctx.send("There is no active D&D game in this channel.")
            return
        
        # Check if user is the creator or the GM
        if str(ctx.author.id) != game["created_by"] and str(ctx.author.id) != game["game_master_id"]:
            await ctx.send("Only the game creator or Game Master can end this game.")
            return
        
        # Delete the game
        await self.delete_game(channel_id)
        await ctx.send("The D&D game has been ended. Thanks for playing!")
    
    def cog_unload(self):
        """Clean up resources when the cog is unloaded"""
        if self.use_mongo:
            self.mongo_client.close()

async def setup(bot):
    await bot.add_cog(DnDGame(bot))