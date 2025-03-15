import discord
from discord.ext import commands
import asyncio
from datetime import datetime

class CharacterCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.parent_cog = None
    
    async def cog_load(self):
        # Get reference to the parent DnDGame cog
        self.parent_cog = self.bot.get_cog("DnDGame")
        if not self.parent_cog:
            print("WARNING: DnDGame cog not found. Character creation requires DnDGame cog.")
    
    @commands.command(name="creation")
    async def character_creation(self, ctx):
        """Create a character for the current D&D game
        
        Example: !creation
        """
        # Check if DnDGame cog is loaded
        if not self.parent_cog:
            await ctx.send("Error: DnD game system is not currently available.")
            return
        
        channel_id = str(ctx.channel.id)
        
        # Check if there's an active game in this channel
        game = await self.parent_cog.get_game(channel_id)
        if not game:
            await ctx.send("There is no active D&D game in this channel. Use `!dnd` to create one first.")
            return
        
        # Check if user is a player in this game
        user_id = str(ctx.author.id)
        if user_id not in game["player_ids"]:
            await ctx.send("You are not a player in this D&D game.")
            return
        
        # Check if characters exist in the game data
        if "characters" not in game:
            game["characters"] = {}
        
        # Check if player already has a character
        if user_id in game["characters"]:
            # Ask if they want to overwrite
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
        
        # Send character creation instructions
        instruction_embed = discord.Embed(
            title="🧙‍♂️ Character Creation 📝",
            description="Please provide your character information in the following format:",
            color=discord.Color.blue()
        )
        
        instruction_embed.add_field(
            name="Character Format",
            value=(
                "**Name:** [Character Name]\n"
                "**Class:** [Character Class]\n"
                "**Level:** 0 (must start at 0)\n"
                "**Race:** [Character Race]\n"
                "**Background:** [Character Background]\n"
                "**Alignment:** [Character Alignment]\n"
                "**Ability Scores:**\n"
                "- **Strength:** [Score]\n"
                "- **Dexterity:** [Score]\n"
                "- **Constitution:** [Score]\n"
                "- **Intelligence:** [Score]\n"
                "- **Wisdom:** [Score]\n"
                "- **Charisma:** [Score]"
            ),
            inline=False
        )
        
        instruction_embed.set_footer(text="Type your character information in a single message.")
        
        await ctx.send(embed=instruction_embed)
        
        # Wait for character creation response
        def check_character(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            character_msg = await self.bot.wait_for('message', check=check_character, timeout=300)
            
            # Parse the character information
            # This is a simple parsing, you may want to enhance it for better validation
            character_data = {
                "raw_input": character_msg.content,
                "created_at": datetime.now().isoformat()
            }
            
            # Parse the character information into structured data
            lines = character_msg.content.split('\n')
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # Map common keys to standard names
                    if "name" in key:
                        character_data["name"] = value
                    elif "class" in key:
                        character_data["class"] = value
                    elif "level" in key:
                        character_data["level"] = value
                    elif "race" in key:
                        character_data["race"] = value
                    elif "background" in key:
                        character_data["background"] = value
                    elif "alignment" in key:
                        character_data["alignment"] = value
                    elif "strength" in key:
                        character_data["strength"] = value
                    elif "dexterity" in key:
                        character_data["dexterity"] = value
                    elif "constitution" in key:
                        character_data["constitution"] = value
                    elif "intelligence" in key:
                        character_data["intelligence"] = value
                    elif "wisdom" in key:
                        character_data["wisdom"] = value
                    elif "charisma" in key:
                        character_data["charisma"] = value
            
            # Check if the essential fields are present
            required_fields = ["name", "class", "level", "race"]
            missing_fields = [field for field in required_fields if field not in character_data]
            
            if missing_fields:
                await ctx.send(f"Missing required fields: {', '.join(missing_fields)}. Please try again.")
                return
            
            # Check if level is 0
            if character_data.get("level", "").strip() != "0":
                await ctx.send("New characters must start at level 0. Please try again.")
                return
            
            # Create character embed
            character_embed = discord.Embed(
                title=f"Character: {character_data.get('name', 'Unknown')}",
                description=f"Created by {ctx.author.display_name}",
                color=discord.Color.green()
            )
            
            # Add character details to embed
            character_embed.add_field(name="Class", value=character_data.get("class", "Unknown"), inline=True)
            character_embed.add_field(name="Level", value=character_data.get("level", "0"), inline=True)
            character_embed.add_field(name="Race", value=character_data.get("race", "Unknown"), inline=True)
            character_embed.add_field(name="Background", value=character_data.get("background", "Unknown"), inline=True)
            character_embed.add_field(name="Alignment", value=character_data.get("alignment", "Unknown"), inline=True)
            
            # Add ability scores
            ability_scores = (
                f"**STR:** {character_data.get('strength', '?')} | "
                f"**DEX:** {character_data.get('dexterity', '?')} | "
                f"**CON:** {character_data.get('constitution', '?')}\n"
                f"**INT:** {character_data.get('intelligence', '?')} | "
                f"**WIS:** {character_data.get('wisdom', '?')} | "
                f"**CHA:** {character_data.get('charisma', '?')}"
            )
            character_embed.add_field(name="Ability Scores", value=ability_scores, inline=False)
            
            # Add character data to the game
            game["characters"][user_id] = character_data
            
            # Update game state
            game["last_updated"] = datetime.now().isoformat()
            await self.parent_cog.save_game(channel_id, game)
            
            await ctx.send(f"Character created successfully for {ctx.author.mention}!", embed=character_embed)
            
        except asyncio.TimeoutError:
            await ctx.send("Character creation timed out. Please try again when you're ready.")
    
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
            await ctx.send("There is no active D&D game in this channel.")
            return
        
        # Check if characters exist in the game data
        if "characters" not in game or user_id not in game["characters"]:
            await ctx.send(f"{member.display_name} doesn't have a character in this game.")
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
            await ctx.send("There is no active D&D game in this channel.")
            return
        
        # Check if characters exist in the game data
        if "characters" not in game or not game["characters"]:
            await ctx.send("No characters have been created in this game yet.")
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