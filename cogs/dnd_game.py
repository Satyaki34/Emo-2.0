import discord
from discord.ext import commands
import asyncio

class DnDGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # Stores active games by channel ID
    
    @commands.command(name="dnd")
    async def dnd_setup(self, ctx):
        """Setup a new Dungeons & Dragons game session
        
        Example: !dnd
        """
        channel_id = str(ctx.channel.id)
        
        # Check if there's already a game in this channel
        if channel_id in self.active_games:
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
                    "players": player_names,
                    "player_ids": player_ids,
                    "game_master": gm_name,
                    "game_master_id": gm_id,
                    "is_ai_gm": is_ai_gm
                }
                
                self.active_games[channel_id] = game_data
                
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

async def setup(bot):
    await bot.add_cog(DnDGame(bot))