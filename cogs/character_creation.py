import discord
from discord.ext import commands
import asyncio
from datetime import datetime

class CharacterCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.parent_cog = None
    
    async def cog_load(self):
        self.parent_cog = self.bot.get_cog("DnDGame")
        if not self.parent_cog:
            print("WARNING: DnDGame cog not found. Character creation requires DnDGame cog.")
    
    @commands.command(name="creation")
    async def character_creation(self, ctx):
        """Create a character for the current D&D game with a guided process
        
        Example: !creation
        """
        if not self.parent_cog:
            await ctx.send("Error: DnD game system is not currently available.")
            return
        
        channel_id = str(ctx.channel.id)
        game = await self.parent_cog.get_game(channel_id)
        if not game:
            await ctx.send("There is no active D&D game in this channel. Use `!dnd` to create one first.")
            return
        
        user_id = str(ctx.author.id)
        if user_id not in game["player_ids"]:
            await ctx.send("You are not a player in this D&D game.")
            return
        
        if "characters" not in game:
            game["characters"] = {}
        
        if user_id in game["characters"]:
            confirm_msg = await ctx.send(f"{ctx.author.mention}, you already have a character. Do you want to create a new one? (yes/no)")
            def check_confirm(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
            try:
                confirm_response = await self.bot.wait_for('message', check=check_confirm, timeout=30)
                if confirm_response.content.lower() != "yes":
                    await ctx.send("Character creation cancelled.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("Character creation timed out.")
                return
        
        # Guided character creation
        character_data = {"level": "0", "created_at": datetime.now().isoformat()}
        steps = [
            ("name", "What’s your character’s **name**? (e.g., 'Thorin')", False),
            ("class", "What **class** is your character? (e.g., 'Fighter', 'Wizard')", False),
            ("race", "What **race** is your character? (e.g., 'Human', 'Elf')", False),
            ("backstory", "What’s your character’s **backstory**? (e.g., 'Raised in the mountains after a dragon attack', optional - press Enter to skip)", True),
            ("alignment", "What’s your character’s **alignment**? (e.g., 'Lawful Good', optional - press Enter to skip)", True),
        ]
        
        await ctx.send("### Let’s create your character step-by-step! Reply to each question. Type '**cancel**' to stop at any time.")
        
        def check_response(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        for key, prompt, optional in steps:
            await ctx.send(prompt)
            try:
                response = await self.bot.wait_for('message', check=check_response, timeout=60)
                if response.content.lower() == "cancel":
                    await ctx.send("### Character creation cancelled.")
                    return
                value = response.content.strip()
                if not value and not optional:
                    await ctx.send(f"### {key.capitalize()} is required. Please try again.")
                    continue
                if value:
                    character_data[key] = value
            except asyncio.TimeoutError:
                await ctx.send(f"### Timed out waiting for {key}. Character creation cancelled.")
                return
        
        # Ability scores with validation
        ability_scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        await ctx.send("### Now, enter your ability scores (3-18). Type each score as a number, one per message.")
        
        for ability in ability_scores:
            while True:
                await ctx.send(f"What’s your **{ability.capitalize()}** score? (3-18, or Enter for 10)")
                try:
                    response = await self.bot.wait_for('message', check=check_response, timeout=60)
                    if response.content.lower() == "cancel":
                        await ctx.send("### Character creation cancelled.")
                        return
                    value = response.content.strip()
                    if not value:
                        character_data[ability] = "10"
                        break
                    try:
                        score = int(value)
                        if 3 <= score <= 18:
                            character_data[ability] = str(score)
                            break
                        else:
                            await ctx.send("### Score must be between 3 and 18. Try again.")
                    except ValueError:
                        await ctx.send("### Please enter a valid number (or Enter for 10).")
                except asyncio.TimeoutError:
                    await ctx.send(f"### Timed out waiting for {ability}. Character creation cancelled.")
                    return
        
        # Final confirmation
        confirm_embed = discord.Embed(
            title="Character Confirmation",
            description="Here’s your character. Reply 'yes' to save, 'no' to cancel.",
            color=discord.Color.blue()
        )
        self._add_character_fields(confirm_embed, character_data, ctx.author.display_name)
        await ctx.send(embed=confirm_embed)
        
        try:
            confirm = await self.bot.wait_for('message', check=check_response, timeout=60)
            if confirm.content.lower() != "yes":
                await ctx.send("### Character creation cancelled.")
                return
        except asyncio.TimeoutError:
            await ctx.send("### Confirmation timed out. Character creation cancelled.")
            return
        
        # Save character
        game["characters"][user_id] = character_data
        game["last_updated"] = datetime.now().isoformat()
        await self.parent_cog.save_game(channel_id, game)
        
        success_embed = discord.Embed(
            title=f"Character: {character_data.get('name', 'Unknown')}",
            description=f"Created by {ctx.author.display_name}",
            color=discord.Color.green()
        )
        self._add_character_fields(success_embed, character_data)
        await ctx.send(f"Character created successfully for {ctx.author.mention}!", embed=success_embed)
    
    def _add_character_fields(self, embed, character_data, author_name=None):
        """Helper to add character fields to an embed"""
        embed.add_field(name="Class", value=character_data.get("class", "Unknown"), inline=True)
        embed.add_field(name="Level", value=character_data.get("level", "0"), inline=True)
        embed.add_field(name="Race", value=character_data.get("race", "Unknown"), inline=True)
        embed.add_field(name="Backstory", value=character_data.get("backstory", "None"), inline=False)
        embed.add_field(name="Alignment", value=character_data.get("alignment", "Neutral"), inline=True)
        ability_scores = (
            f"**STR:** {character_data.get('strength', '10')} | "
            f"**DEX:** {character_data.get('dexterity', '10')} | "
            f"**CON:** {character_data.get('constitution', '10')}\n"
            f"**INT:** {character_data.get('intelligence', '10')} | "
            f"**WIS:** {character_data.get('wisdom', '10')} | "
            f"**CHA:** {character_data.get('charisma', '10')}"
        )
        embed.add_field(name="Ability Scores", value=ability_scores, inline=False)
        if author_name:
            embed.set_footer(text=f"Created by {author_name}")  # Move 'Created by' to footer
    
    @commands.command(name="view_character")
    async def view_character(self, ctx, member: discord.Member = None):
        """View a character in the current D&D game
        
        Example: !view_character @username
        """
        if not self.parent_cog:
            await ctx.send("Error: DnD game system is not currently available.")
            return
        
        # If no member specified, show the caller's character
        if member is None:
            member = ctx.author
        
        channel_id = str(ctx.channel.id)
        user_id = str(member.id)
        
        # Check if there's an active game in this channel
        game = await self.parent_cog.get_game(channel_id)
        if not game:
            await ctx.send("### There is no active D&D game in this channel.")
            return
        
        # Check if characters exist in the game data
        if "characters" not in game or user_id not in game["characters"]:
            await ctx.send(f"### {member.display_name} doesn't have a character in this game.")
            return
        
        # Get character data
        character = game["characters"][user_id]
        
        # Create character embed
        character_embed = discord.Embed(
            title=f"Character: {character.get('name', 'Unknown')}",
            description=f"Player: {member.display_name}",
            color=discord.Color.blue()
        )
        
        # Add character details to embed
        character_embed.add_field(name="Class", value=character.get("class", "Unknown"), inline=True)
        character_embed.add_field(name="Level", value=character.get("level", "0"), inline=True)
        character_embed.add_field(name="Race", value=character.get("race", "Unknown"), inline=True)
        character_embed.add_field(name="Background", value=character.get("background", "Unknown"), inline=True)
        character_embed.add_field(name="Alignment", value=character.get("alignment", "Unknown"), inline=True)
        
        # Add ability scores
        ability_scores = (
            f"**STR:** {character.get('strength', '?')} | "
            f"**DEX:** {character.get('dexterity', '?')} | "
            f"**CON:** {character.get('constitution', '?')}\n"
            f"**INT:** {character.get('intelligence', '?')} | "
            f"**WIS:** {character.get('wisdom', '?')} | "
            f"**CHA:** {character.get('charisma', '?')}"
        )
        character_embed.add_field(name="Ability Scores", value=ability_scores, inline=False)
        
        await ctx.send(embed=character_embed)
    
    @commands.command(name="list_characters")
    async def list_characters(self, ctx):
        """List all characters in the current D&D game
        
        Example: !list_characters
        """
        if not self.parent_cog:
            await ctx.send("Error: DnD game system is not currently available.")
            return
        
        channel_id = str(ctx.channel.id)
        
        # Check if there's an active game in this channel
        game = await self.parent_cog.get_game(channel_id)
        if not game:
            await ctx.send("### There is no active D&D game in this channel.")
            return
        
        # Check if characters exist in the game data
        if "characters" not in game or not game["characters"]:
            await ctx.send("### No characters have been created in this game yet.")
            return
        
        # Create character list embed
        embed = discord.Embed(
            title="🎭 D&D Characters 🎭",
            description=f"Characters in this game:",
            color=discord.Color.purple()
        )
        
        # Add each character to the list
        for user_id, character in game["characters"].items():
            player = self.bot.get_user(int(user_id))
            player_name = player.display_name if player else "Unknown Player"
            
            embed.add_field(
                name=f"{character.get('name', 'Unknown')}",
                value=(
                    f"Player: {player_name}\n"
                    f"Race: {character.get('race', 'Unknown')}\n"
                    f"Class: {character.get('class', 'Unknown')}\n"
                    f"Level: {character.get('level', '0')}"
                ),
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CharacterCreation(bot))