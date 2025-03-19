import discord
from discord.ext import commands
import asyncio
import random
from discord import ui
from datetime import datetime
from character_images import CHARACTER_IMAGES, DEFAULT_IMAGE

class RaceDropdown(ui.Select):
    def __init__(self):
        races = [
            "Human", "Elf", "Dwarf", "Halfling", "Gnome",
            "Dragonborn", "Tiefling", "Half-Elf", "Half-Orc"
        ]
        options = [discord.SelectOption(label=race, value=race) for race in races]
        super().__init__(
            placeholder="Choose your race...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction
        self.view.selected_race = self.values[0]
        embed = interaction.message.embeds[0]
        embed.description = f"Race selected: **{self.values[0]}**"
        await interaction.message.edit(embed=embed, view=None)
        self.view.stop()

class ClassDropdown(ui.Select):
    def __init__(self):
        classes = [
            "Artificer", "Barbarian", "Bard", "Cleric", "Druid",
            "Fighter", "Monk", "Paladin", "Ranger", "Rogue",
            "Sorcerer", "Warlock", "Wizard"
        ]
        options = [discord.SelectOption(label=cls, value=cls) for cls in classes]
        super().__init__(
            placeholder="Choose your class...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction
        self.view.selected_class = self.values[0]
        embed = interaction.message.embeds[0]
        embed.description = f"Class selected: **{self.values[0]}**"
        await interaction.message.edit(embed=embed, view=None)
        self.view.stop()

class SelectionView(ui.View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_race = None
        self.selected_class = None
    
    async def on_timeout(self):
        self.stop()

class CharacterCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.parent_cog = None
        self.character_images = CHARACTER_IMAGES
        self.default_image = DEFAULT_IMAGE
        
        # Add these lists for random character data
        self.names = [
            "Aelar", "Bryn", "Cora", "Dren", "Elara", "Finn", "Gorrim", "Halia",
            "Ilyana", "Jorik", "Kael", "Liora", "Mira", "Nero", "Oren", "Prynn"
        ]

        self.backstories = [
            "Raised by wolves in the wild forest.",
            "Orphaned and trained by a secretive guild.",
            "A noble's child who ran away from home.",
            "Survived a shipwreck and washed ashore.",
            "Born during a rare celestial event."
        ]

        self.alignments = [
            "Lawful Good", "Neutral Good", "Chaotic Good",
            "Lawful Neutral", "True Neutral", "Chaotic Neutral",
            "Lawful Evil", "Neutral Evil", "Chaotic Evil"
        ]
    
    def normalize_race(self, race):
        """Normalize race names to match character_images.py keys"""
        if "-" in race:
            parts = race.split("-")
            return "-".join([parts[0], parts[1].lower()])
        return race
    
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
            confirm_embed = discord.Embed(
                title="⚔️ Replace Character?",
                description=f"{ctx.author.mention}, you already have a character. Want to create a new one?",
                color=discord.Color.gold()
            )
            confirm_embed.add_field(name="Reply", value="Type `yes` or `no`", inline=False)
            confirm_msg = await ctx.send(embed=confirm_embed)
            def check_confirm(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
            try:
                confirm_response = await self.bot.wait_for('message', check=check_confirm, timeout=30)
                if confirm_response.content.lower() != "yes":
                    await ctx.send("Character creation cancelled.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("Timed out. Character creation cancelled.")
                return
        
        # Start character creation
        character_data = {"level": "1", "created_at": datetime.now().isoformat()}
        intro_embed = discord.Embed(
            title="✨ Character Creation ✨",
            description="Let's craft your D&D legend step-by-step! Answer each prompt below.\nType `cancel` at any text step to stop.",
            color=discord.Color.blue()
        )
        intro_embed.set_footer(text=f"For {ctx.author.display_name}")
        await ctx.send(embed=intro_embed)
        
        def check_response(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        # Step 1: Name
        name_embed = discord.Embed(
            title="🗡️ Step 1/6: Character Name",
            description="What's your character's name?\n**Example:** Thorin",
            color=discord.Color.blue()
        )
        name_embed.add_field(name="Instructions", value="Reply with the name below.", inline=False)
        await ctx.send(embed=name_embed)
        try:
            response = await self.bot.wait_for('message', check=check_response, timeout=60)
            if response.content.lower() == "cancel":
                await ctx.send("Character creation cancelled.")
                return
            name = response.content.strip()
            if not name:
                await ctx.send("Name is required. Character creation cancelled.")
                return
            character_data["name"] = name
        except asyncio.TimeoutError:
            await ctx.send("Timed out waiting for name. Character creation cancelled.")
            return
        
        # Step 2: Class
        class_embed = discord.Embed(
            title="⚒️ Step 2/6: Character Class",
            description="What's your character's class?",
            color=discord.Color.blue()
        )
        class_view = SelectionView()
        class_view.add_item(ClassDropdown())
        class_msg = await ctx.send(embed=class_embed, view=class_view)
        await class_view.wait()
        if not class_view.selected_class:
            await class_msg.edit(content="Timed out waiting for class selection. Character creation cancelled.", embed=None, view=None)
            return
        character_data["class"] = class_view.selected_class
        
        # Step 3: Race
        race_embed = discord.Embed(
            title="🌍 Step 3/6: Character Race",
            description="What's your character's race?",
            color=discord.Color.blue()
        )
        race_view = SelectionView()
        race_view.add_item(RaceDropdown())
        race_msg = await ctx.send(embed=race_embed, view=race_view)
        await race_view.wait()
        if not race_view.selected_race:
            await race_msg.edit(content="Timed out waiting for race selection. Character creation cancelled.", embed=None, view=None)
            return
        character_data["race"] = race_view.selected_race
        
        # Step 4: Backstory
        backstory_embed = discord.Embed(
            title="📜 Step 4/6: Backstory",
            description="What's your character's backstory?\n**Example:** Raised in the mountains after a dragon attack, Abandoned as a sacrifice to ancient forest spirits and raised by them to become their vengeful champion, etc.",
            color=discord.Color.blue()
        )
        backstory_embed.add_field(name="Instructions", value="Reply with the backstory below.", inline=False)
        await ctx.send(embed=backstory_embed)
        try:
            response = await self.bot.wait_for('message', check=check_response, timeout=60)
            if response.content.lower() == "cancel":
                await ctx.send("Character creation cancelled.")
                return
            backstory = response.content.strip()
            if backstory:
                character_data["backstory"] = backstory
        except asyncio.TimeoutError:
            await ctx.send("Timed out waiting for backstory. Character creation cancelled.")
            return
        
        # Step 5: Alignment
        alignment_embed = discord.Embed(
            title="⚖️ Step 5/6: Alignment",
            description="What's your character's alignment?\n**Example:** Lawful Good, Neutral Evil, etc.",
            color=discord.Color.blue()
        )
        alignment_embed.add_field(name="Instructions", value="Reply with the alignment below.", inline=False)
        await ctx.send(embed=alignment_embed)
        try:
            response = await self.bot.wait_for('message', check=check_response, timeout=60)
            if response.content.lower() == "cancel":
                await ctx.send("Character creation cancelled.")
                return
            alignment = response.content.strip()
            if alignment:
                character_data["alignment"] = alignment
        except asyncio.TimeoutError:
            await ctx.send("Timed out waiting for alignment. Character creation cancelled.")
            return
        
        # Step 6: Ability Scores
        ability_scores = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        scores_embed = discord.Embed(
            title="💪 Step 6/6: Ability Scores",
            description="You have 18 points to assign to your abilities. Each ability starts at 10, and you can assign up to 7 points per ability.\n" +
                        "You will be prompted for each ability one by one. Reply with the number of points to assign (0 to 7) for each.",
            color=discord.Color.blue()
        )
        scores_embed.add_field(name="Instructions", value="Wait for the prompts for each ability.", inline=False)
        await ctx.send(embed=scores_embed)
        
        ability_values = {ability.lower(): 10 for ability in ability_scores}
        remaining_points = 18
        
        for ability in ability_scores:
            ability_key = ability.lower()
            if remaining_points == 0:
                character_data[ability_key] = "10"
                continue
            while True:
                current_scores = "\n".join([f"{abl.capitalize()}: {ability_values[abl.lower()]}" for abl in ability_scores])
                embed = discord.Embed(
                    title=f"Assign points to {ability}",
                    description=f"Current scores:\n{current_scores}\n\nRemaining points: {remaining_points}\n\nHow many points do you want to assign to {ability}? (0 to {min(7, remaining_points)})",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                try:
                    response = await self.bot.wait_for('message', check=check_response, timeout=60)
                    if response.content.lower() == "cancel":
                        await ctx.send("Character creation cancelled.")
                        return
                    points_str = response.content.strip()
                    try:
                        points = int(points_str)
                        if 0 <= points <= min(7, remaining_points):
                            ability_values[ability_key] += points
                            remaining_points -= points
                            character_data[ability_key] = str(ability_values[ability_key])
                            break
                        else:
                            await ctx.send(f"Invalid points. Must be between 0 and {min(7, remaining_points)}.")
                    except ValueError:
                        await ctx.send("Please enter a valid number.")
                except asyncio.TimeoutError:
                    await ctx.send("Timed out. Character creation cancelled.")
                    return
        if remaining_points > 0:
            await ctx.send(f"You have {remaining_points} points left unassigned.")
        
        # Final confirmation
        confirm_embed = discord.Embed(
            title="✅ Character Confirmation",
            description="Here's your character! Reply `yes` to save, `no` to cancel.",
            color=discord.Color.gold()
        )
        self._add_character_fields(confirm_embed, character_data, ctx.author.display_name)
        await ctx.send(embed=confirm_embed)
        
        try:
            confirm = await self.bot.wait_for('message', check=check_response, timeout=60)
            if confirm.content.lower() != "yes":
                await ctx.send("Character creation cancelled.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Confirmation timed out. Character creation cancelled.")
            return
        
        # Save character
        game["characters"][user_id] = character_data
        game["last_updated"] = datetime.now().isoformat()
        await self.parent_cog.save_game(channel_id, game)
        
        # Success embed
        success_embed = discord.Embed(
            title=f"🎉 Character: {character_data.get('name', 'Unknown')}",
            description=f"Created by {ctx.author.display_name}",
            color=discord.Color.green()
        )
        self._add_character_fields(success_embed, character_data)
        image_key = f"{character_data['race']}_{character_data['class']}"
        image_url = self.character_images.get(image_key, self.default_image)
        success_embed.set_thumbnail(url=image_url)
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
            embed.set_footer(text=f"Created by {author_name}")
 
    @commands.command(name="view_character")
    async def view_character(self, ctx, member: discord.Member = None):
        """View a character in the current D&D game
        
        Example: !view_character @username
        """
        if not self.parent_cog:
            await ctx.send("Error: DnD game system is not currently available.")
            return
        
        if member is None:
            member = ctx.author
        
        channel_id = str(ctx.channel.id)
        user_id = str(member.id)
        
        game = await self.parent_cog.get_game(channel_id)
        if not game:
            await ctx.send("### There is no active D&D game in this channel.")
            return
        
        if "characters" not in game or user_id not in game["characters"]:
            await ctx.send(f"### {member.display_name} doesn't have a character in this game.")
            return
        
        character = game["characters"][user_id]
        
        character_embed = discord.Embed(
            title=f"Character: {character.get('name', 'Unknown')}",
            description=f"Player: {member.display_name}",
            color=discord.Color.blue()
        )
        
        self._add_character_fields(character_embed, character, member.display_name)
        
        image_key = f"{character['race']}_{character['class']}"
        image_url = self.character_images.get(image_key, self.default_image)
        character_embed.set_thumbnail(url=image_url)
        
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
        
        game = await self.parent_cog.get_game(channel_id)
        if not game:
            await ctx.send("### There is no active D&D game in this channel.")
            return
        
        if "characters" not in game or not game["characters"]:
            await ctx.send("### No characters have been created in this game yet.")
            return
        
        embed = discord.Embed(
            title="🎭 D&D Characters 🎭",
            description=f"Characters in this game:",
            color=discord.Color.purple()
        )
        
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
    
    @commands.command(name="random")
    async def random_character(self, ctx):
        """Generate a random D&D character and ask for confirmation
        
        Example: !random
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

        # Generate random character
        character_data = self.generate_random_character()

        # Display character and ask for confirmation
        await self.display_and_confirm(ctx, character_data, game, user_id)

    def generate_random_character(self):
        """Generate random character data"""
        races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Dragonborn", "Tiefling", "Half-Elf", "Half-Orc"]
        classes = ["Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]
        ability_scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

        character_data = {
            "name": random.choice(self.names),
            "class": random.choice(classes),
            "race": random.choice(races),
            "backstory": random.choice(self.backstories),
            "alignment": random.choice(self.alignments),
            "level": "1",
            "skills": "Random skills based on class and race",  # Placeholder
            "inventory": "Random inventory based on class and race",  # Placeholder
            "spells": "Random spells based on class and race",  # Placeholder
            "created_at": datetime.now().isoformat()
        }

        # Generate ability scores (4d6 drop lowest)
        for ability in ability_scores:
            rolls = [random.randint(1, 6) for _ in range(4)]
            rolls.sort()
            score = sum(rolls[1:])  # Drop the lowest roll
            character_data[ability] = str(score)

        return character_data

    async def display_and_confirm(self, ctx, character_data, game, user_id):
        """Display character and ask for confirmation"""
        embed = discord.Embed(
            title=f"🎲 Random Character: {character_data['name']}",
            description="Here's your randomly generated character! Type `yes` to accept or `no` to reroll.",
            color=discord.Color.gold()
        )
        self._add_character_fields(embed, character_data)
        embed.add_field(name="Skills", value=character_data.get("skills", "None"), inline=False)
        embed.add_field(name="Inventory", value=character_data.get("inventory", "None"), inline=False)
        embed.add_field(name="Spells", value=character_data.get("spells", "None"), inline=False)
        normalized_race = self.normalize_race(character_data['race'])
        image_key = f"{normalized_race}_{character_data['class']}"
        image_url = self.character_images.get(image_key, self.default_image)
        embed.set_thumbnail(url=image_url)
        await ctx.send(embed=embed)

        # Get the channel_id from the context
        channel_id = str(ctx.channel.id)

        def check_confirm(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

        try:
            confirm = await self.bot.wait_for('message', check=check_confirm, timeout=60)
            if confirm.content.lower() == "yes":
                game["characters"][user_id] = character_data
                game["last_updated"] = datetime.now().isoformat()
                await self.parent_cog.save_game(channel_id, game)
                await ctx.send(f"Character {character_data['name']} accepted and saved!")
            else:
                await ctx.send("Rerolling for a new character...")
                new_character = self.generate_random_character()
                await self.display_and_confirm(ctx, new_character, game, user_id)
        except asyncio.TimeoutError:
            await ctx.send("Confirmation timed out. Character creation cancelled.")

async def setup(bot):
    await bot.add_cog(CharacterCreation(bot))