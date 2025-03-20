import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
import os
import random
import json
from dotenv import load_dotenv
from datetime import datetime
from discord import ui

class InventoryDropdown(ui.Select):
    def __init__(self, options, index):
        self.index = index
        super().__init__(
            placeholder="Choose an item...",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=opt.strip(), value=opt.strip()) for opt in options]
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_inventory[self.index] = self.values[0]

class SkillsDropdown(ui.Select):
    def __init__(self, skill_options, choose_count):
        self.choose_count = choose_count
        options = [discord.SelectOption(label=skill, value=skill) for skill in skill_options]
        super().__init__(
            placeholder=f"Choose {choose_count} skills...",
            min_values=choose_count,
            max_values=choose_count,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_skills = self.values  # Store selection, but don't stop the view

class SpellsDropdown(ui.Select):
    def __init__(self, spell_type, options, choose_count):
        self.choose_count = choose_count
        self.spell_type = spell_type
        placeholder = f"Choose {choose_count} {spell_type}s..."
        options = [discord.SelectOption(label=spell, value=spell) for spell in options]
        super().__init__(
            placeholder=placeholder,
            min_values=choose_count,
            max_values=choose_count,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.spell_type == "Cantrip":
            self.view.selected_cantrips = self.values
        else:
            self.view.selected_spells = self.values  # Store selection, but don't stop the view

class SelectionView(ui.View):
    def __init__(self, player_id, inventory_length, selection_type=None, choose_count=None, timeout=60):
        super().__init__(timeout=timeout)
        self.player_id = player_id
        self.selected_inventory = [None] * inventory_length if selection_type == "inventory" else None
        self.selected_skills = None
        self.selected_cantrips = None
        self.selected_spells = None
        self.selection_type = selection_type
        self.choose_count = choose_count if selection_type in ["skills", "cantrips", "spells"] else None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(self.player_id)
    
    async def on_timeout(self):
        self.stop()

class ConfirmButton(ui.Button):
    def __init__(self):
        super().__init__(label="Confirm", style=discord.ButtonStyle.green)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Validate selections based on selection_type
        if self.view.selection_type == "inventory" and None in self.view.selected_inventory:
            await interaction.followup.send("Please select one option from each equipment choice before confirming.", ephemeral=True)
            return
        elif self.view.selection_type == "skills" and (not self.view.selected_skills or len(self.view.selected_skills) < self.view.choose_count):
            await interaction.followup.send(f"Please select {self.view.choose_count} skills before confirming.", ephemeral=True)
            return
        elif self.view.selection_type == "cantrips" and (not self.view.selected_cantrips or len(self.view.selected_cantrips) < self.view.choose_count):
            await interaction.followup.send(f"Please select {self.view.choose_count} cantrips before confirming.", ephemeral=True)
            return
        elif self.view.selection_type == "spells" and (not self.view.selected_spells or len(self.view.selected_spells) < self.view.choose_count):
            await interaction.followup.send(f"Please select {self.view.choose_count} spells before confirming.", ephemeral=True)
            return
        
        self.view.stop()

class DnDGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')
        
        if not mongo_uri:
            print("WARNING: MONGO_URI not found in .env file!")
            self.use_mongo = False
            self.active_games = {}
        else:
            try:
                self.mongo_client = MongoClient(mongo_uri)
                self.db = self.mongo_client['emo_bot']
                self.games_collection = self.db['dnd_games']
                self.games_collection.create_index("channel_id", unique=True)
                self.use_mongo = True
                print("Successfully connected to MongoDB for DnD games")
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                self.use_mongo = False
                self.active_games = {}
                
        self.gemini_model = None
    
    async def setup_gemini_model(self):
        if not self.gemini_model:
            gemini_cog = self.bot.get_cog('GeminiChat')
            if gemini_cog and hasattr(gemini_cog, 'model'):
                self.gemini_model = gemini_cog.model
                print("Successfully connected to Gemini model for DnD features")
            else:
                print("WARNING: GeminiChat cog not found or has no 'model' attribute.")
    
    async def get_gemini_response(self, system_prompt, user_prompt, history=None):
        await self.setup_gemini_model()
        if not self.gemini_model:
            return "Sorry, my storytelling brain isn't working right now. Check if GeminiChat is set up correctly!"
        
        try:
            chat = self.gemini_model.start_chat(history=[])
            await asyncio.to_thread(chat.send_message, system_prompt)
            response = await asyncio.to_thread(chat.send_message, user_prompt)
            return response.text
        except Exception as e:
            print(f"Error getting Gemini response: {e}")
            return "Sorry, I tripped over my own code. Try again!"

    async def get_game(self, channel_id):
        if not self.use_mongo:
            return self.active_games.get(str(channel_id))
        else:
            return self.games_collection.find_one({"channel_id": str(channel_id)})
    
    async def save_game(self, channel_id, game_data):
        if not self.use_mongo:
            self.active_games[str(channel_id)] = game_data
        else:
            self.games_collection.update_one(
                {"channel_id": str(channel_id)},
                {"$set": game_data},
                upsert=True
            )
    
    async def delete_game(self, channel_id):
        if not self.use_mongo:
            if str(channel_id) in self.active_games:
                del self.active_games[str(channel_id)]
        else:
            self.games_collection.delete_one({"channel_id": str(channel_id)})
    
    async def add_to_game_history(self, channel_id, entry):
        game = await self.get_game(channel_id)
        if game:
            if "history" not in game:
                game["history"] = []
            game["history"].append(entry)
            if len(game["history"]) > 20:
                game["history"] = game["history"][-20:]
            await self.save_game(channel_id, game)
    
    @commands.command(name="dnd")
    async def dnd_setup(self, ctx):
        channel_id = str(ctx.channel.id)
        existing_game = await self.get_game(channel_id)
        if existing_game:
            await ctx.send("A D&D game is already set up in this channel.")
            return
        
        embed = discord.Embed(
            title="🎲 D&D Game Setup 🐉",
            description="Let's set up your Dungeons & Dragons game!",
            color=discord.Color.dark_purple()
        )
        await ctx.send(embed=embed)
        
        await ctx.send("**Step 1:** Please tag all `players` who will participate (including `yourself` if you're playing)")
        
        def check_message(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            player_msg = await self.bot.wait_for('message', check=check_message, timeout=60)
            mentioned_players = player_msg.mentions
            if not mentioned_players:
                await ctx.send("No players were mentioned. Game setup cancelled.")
                return
            
            player_names = [player.display_name for player in mentioned_players]
            player_ids = [str(player.id) for player in mentioned_players]
            
            gm_embed = discord.Embed(
                title="Game Master Selection:-",
                description="Who will be the Game Master (DM)?",
                color=discord.Color.dark_purple()
            )
            options = "**0.** Emo (AI Game Master)\n"
            for i, player in enumerate(player_names, 1):
                options += f"**{i}.** {player}\n"
            gm_embed.add_field(name="Options:", value=options)
            await ctx.send(embed=gm_embed)
            await ctx.send("Enter the `number` of your choice:")
            
            gm_choice_msg = await self.bot.wait_for('message', check=check_message, timeout=60)
            try:
                choice = int(gm_choice_msg.content.strip())
                if choice < 0 or choice > len(player_names):
                    await ctx.send("Invalid choice. Game setup cancelled.")
                    return
                
                if choice == 0:
                    gm_name = "Emo"
                    gm_id = str(self.bot.user.id)
                    is_ai_gm = True
                else:
                    gm_name = player_names[choice-1]
                    gm_id = player_ids[choice-1]
                    is_ai_gm = False
                
                success_embed = discord.Embed(
                    title="🎲 D&D Game Created! 🐉",
                    description="Your game has been set up successfully!",
                    color=discord.Color.green()
                )
                player_list = ", ".join(player_names)
                success_embed.add_field(name="Players", value=player_list)
                success_embed.add_field(name="Game Master", value=gm_name)
                
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
                    "last_updated": ctx.message.created_at.isoformat(),
                    "characters": {},
                    "campaign": None,
                    "current_scene": None,
                    "npcs": [],
                    "quests": [],
                    "combat": {"active": False, "participants": [], "current_turn": 0, "round": 0},
                    "history": []
                }
                await self.save_game(channel_id, game_data)
                
                await ctx.send(embed=success_embed)
                if is_ai_gm:
                    await ctx.send("**Emo** will be your Game Master! Use `!campaign_setup` to start creating your adventure (Use `!creation` or `!random` to create/generate a character)")
                else:
                    await ctx.send(f"{gm_name} will be your Game Master! More **D&D commands** will be available soon.")
                
            except ValueError:
                await ctx.send("Please enter a valid number. Game setup cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("Setup timed out. Please try again when you're ready.")
    
    @commands.command(name="dnd_status")
    async def dnd_status(self, ctx):
        channel_id = str(ctx.channel.id)
        game = await self.get_game(channel_id)
        if not game:
            await ctx.send("There is no active D&D game in this channel. Use `!dnd` to create one.")
            return
        
        embed = discord.Embed(
            title="🎲 D&D Game Status 🐉",
            description="Current game information:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Game Master", value=game["game_master"], inline=True)
        embed.add_field(name="Players", value=", ".join(game["players"]), inline=False)
        embed.add_field(name="State", value=game["state"].capitalize(), inline=True)
        if game.get("campaign"):
            embed.add_field(name="Campaign", value=game["campaign"].get("name", "Unnamed"), inline=True)
        if game.get("characters"):
            embed.add_field(name="Characters", value=f"{len(game['characters'])} created", inline=True)
        if game.get("current_scene"):
            embed.add_field(name="Current Scene", value=game["current_scene"].get("name", "Unknown"), inline=True)
        if game.get("combat", {}).get("active", False):
            embed.add_field(name="Combat", value=f"Active - Round {game['combat']['round']}", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="end_dnd")
    async def end_dnd(self, ctx):
        channel_id = str(ctx.channel.id)
        
        if isinstance(ctx.channel, discord.Thread):
            thread_id = channel_id
            ic_channel_id = str(ctx.channel.parent_id)
            
            # Find the game where this thread is the OOC thread
            game = None
            for stored_game in (self.active_games.values() if not self.use_mongo else self.games_collection.find()):
                if stored_game.get("ooc_thread_id") == thread_id and stored_game.get("ic_channel_id") == ic_channel_id:
                    game = stored_game
                    break
            
            if not game:
                await ctx.send("No active D&D game found associated with this thread.")
                return
            
            if str(ctx.author.id) != game["created_by"] and str(ctx.author.id) != game["game_master_id"]:
                await ctx.send("Only the game creator or Game Master can end this game.")
                return
            
            # Delete the IC channel and OOC thread
            guild = ctx.guild
            if "ic_channel_id" in game:
                ic_channel = guild.get_channel(int(game["ic_channel_id"]))
                if ic_channel:
                    await ic_channel.delete()
                else:
                    print(f"Warning: IC channel {game['ic_channel_id']} not found for deletion.")
            
            if "ooc_thread_id" in game:
                ooc_thread = guild.get_channel_or_thread(int(game["ooc_thread_id"]))
                if ooc_thread and ooc_thread != ctx.channel:
                    await ooc_thread.delete()
            
            await self.delete_game(game["channel_id"])
            await ctx.send("The D&D game has ended. The IC channel and OOC thread will be deleted. Thanks for playing!")
        
        else:
            game = await self.get_game(channel_id)
            if not game:
                await ctx.send("There is no active D&D game in this channel.")
                return
            
            if str(ctx.author.id) != game["created_by"] and str(ctx.author.id) != game["game_master_id"]:
                await ctx.send("Only the game creator or Game Master can end this game.")
                return
            
            if "ic_channel_id" in game or "ooc_thread_id" in game:
                await ctx.send("This game has started. Please use `!end_dnd` in the OOC thread to end it.")
                return
            
            await self.delete_game(channel_id)
            await ctx.send("The D&D game has been ended before starting. Thanks for playing!")
    
    @commands.command(name="campaign_setup")
    async def campaign_setup(self, ctx):
        """Sets up the campaign theme and welcomes players with character info and choices."""
        channel_id = str(ctx.channel.id)
        game = await self.get_game(channel_id)
        
        if not game:
            await ctx.send("There is no active D&D game in this channel. Use `!dnd` to create one first.")
            return
        
        if not game["is_ai_gm"]:
            await ctx.send("This command is only available for games with Emo as the Game Master.")
            return
        
        if game["state"] != "setup":
            await ctx.send("The campaign can only be set up during the initial setup phase.")
            return
        
        if str(ctx.author.id) != game["created_by"] and str(ctx.author.id) != game["game_master_id"]:
            await ctx.send("Only the game creator or Game Master (DM) can set up the campaign.")
            return
        
        missing_characters = []
        for player_id in game["player_ids"]:
            if player_id not in game.get("characters", {}):
                player = self.bot.get_user(int(player_id))
                player_name = player.display_name if player else f"User {player_id}"
                missing_characters.append(player_name)
        
        if missing_characters:
            missing_str = ", ".join(missing_characters)
            await ctx.send(f"Please make your character first using `!creation` or `!random`. Players without characters: {missing_str}")
            return
        
        embed = discord.Embed(
            title="📜 Campaign Theme Selection 📜",
            description="Let's set the tone for your adventure!",
            color=discord.Color.dark_gold()
        )
        embed.add_field(
            name="Instructions",
            value="Please provide a theme for the campaign (e.g., 'Dark Fantasy', 'Pirate Adventure')."
        )
        await ctx.send(embed=embed)
        
        def check_message(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            theme_msg = await self.bot.wait_for('message', check=check_message, timeout=60)
            theme = theme_msg.content.strip()
            if not theme:
                await ctx.send("No theme provided. Campaign setup cancelled.")
                return
            
            player_mentions = ", ".join(f"<@{player_id}>" for player_id in game["player_ids"])
            welcome_msg = (
                f"Welcome, players {player_mentions}! I am Emo, your Game Master for this {theme} adventure. "
                f"Prepare for an epic journey!"
            )
            followup_msg = "I’ve sent every player some special choices for their characters. Check them out!!"
            
            game["theme"] = theme
            game["state"] = "active"
            game["last_updated"] = datetime.now().isoformat()
            await self.save_game(channel_id, game)
            
            await ctx.send(welcome_msg)
            await ctx.send(followup_msg)
            
            from character_data import RACES, CLASSES
            
            race_mapping = {
                "Human": "Human",
                "Elf": "Elf (High Elf)",
                "Dwarf": "Dwarf (Mountain Dwarf)",
                "Halfling": "Halfling (Lightfoot)",
                "Gnome": "Gnome (Rock)",
                "Dragonborn": "Dragonborn",
                "Tiefling": "Tiefling",
                "Half-Elf": "Half-Elf",
                "Half-Orc": "Half-Orc"
            }
            
            completed_players = set()
            
            for player_id in game["player_ids"]:
                player = self.bot.get_user(int(player_id))
                if not player:
                    await ctx.send(f"Error: Could not find user <@{player_id}>.")
                    continue
                
                character = game["characters"][player_id]
                race_key = race_mapping.get(character["race"].split()[0], character["race"])
                if race_key not in RACES:
                    await ctx.send(f"Error: Invalid race '{character['race']}' for <@{player_id}>.")
                    continue
                
                race_data = RACES[race_key]
                class_data = CLASSES[character["class"]]
        
                character["languages"] = race_data["languages"]
                character["traits"] = race_data["traits"]
                character["class_features"] = class_data["class_features"]
                
                # Initial embed with fixed inventory
                intro_msg = (
                    f"Hail, noble adventurer! Here are some special choices for your character, "
                    f"{character['name']}, to prepare for the {theme} adventure!"
                )
                char_embed = discord.Embed(
                    title=f"Character: {character['name']}",
                    description=f"A {character['race']} {character['class']}",
                    color=discord.Color.gold()
                )
                char_embed.add_field(name="Languages", value=", ".join(race_data["languages"]), inline=True)
                
                # Split inventory into fixed and choosable
                inventory_options = class_data["equipment"]
                fixed_items = [item.strip() for item in inventory_options if " OR " not in item]
                choosable_pairs = [item.strip() for item in inventory_options if " OR " in item]
                char_embed.add_field(name="Inventory", value=", ".join(fixed_items) or "None yet", inline=True)
                char_embed.add_field(name="Traits", value=", ".join(race_data["traits"]), inline=False)
                char_embed.add_field(name="Class Features", value=", ".join(class_data["class_features"]), inline=False)
                
                ability_scores = (
                    f"STR: {character.get('strength', '10')} | "
                    f"DEX: {character.get('dexterity', '10')} | "
                    f"CON: {character.get('constitution', '10')}\n"
                    f"INT: {character.get('intelligence', '10')} | "
                    f"WIS: {character.get('wisdom', '10')} | "
                    f"CHA: {character.get('charisma', '10')}"
                )
                char_embed.add_field(name="Ability Scores", value=ability_scores, inline=False)
                
                # Handle choosable inventory
                if choosable_pairs:
                    char_embed.add_field(
                        name="Choosable Equipment",
                        value=", ".join(choosable_pairs) + "\n**Choose one from each**",
                        inline=False
                    )
                    view = SelectionView(player_id, len(choosable_pairs), selection_type="inventory")
                    for i, pair in enumerate(choosable_pairs):
                        options = [opt.strip() for opt in pair.split(" OR ")]
                        view.add_item(InventoryDropdown(options, i))
                    view.add_item(ConfirmButton())
                    await player.send(intro_msg, embed=char_embed, view=view)
                    await view.wait()
                    selected_inventory = fixed_items.copy()
                    chosen_items = []
                    for i, pair in enumerate(choosable_pairs):
                        options = [opt.strip() for opt in pair.split(" OR ")]
                        chosen = view.selected_inventory[i]
                        if chosen is None:
                            chosen = options[0]
                        chosen_items.append(chosen)
                        selected_inventory.append(chosen)
                    character["inventory"] = selected_inventory
                    for idx, field in enumerate(char_embed.fields):
                        if field.name == "Inventory":
                            char_embed.set_field_at(
                                idx,
                                name="Inventory",
                                value=", ".join(selected_inventory),
                                inline=True
                            )
                            break
                    for idx, field in enumerate(char_embed.fields):
                        if field.name == "Choosable Equipment":
                            char_embed.remove_field(idx)
                            break
                    char_embed.add_field(
                        name="Chosen Equipment",
                        value="Your chosen items are locked: " + ", ".join(chosen_items),
                        inline=False
                    )
                    intro_msg = f"Your inventory for {character['name']} is set!"
                    await player.send(intro_msg, embed=char_embed)
                else:
                    character["inventory"] = fixed_items
                
                # Handle skills
                if "skills" in class_data and class_data["skills"]["choose"] > 0:
                    char_embed.add_field(
                        name=f"Skills (Choose {class_data['skills']['choose']})",
                        value=", ".join(class_data["skills"]["options"]),
                        inline=False
                    )
                    view = SelectionView(player_id, 0, selection_type="skills", choose_count=class_data["skills"]["choose"])
                    view.add_item(SkillsDropdown(class_data["skills"]["options"], class_data["skills"]["choose"]))
                    view.add_item(ConfirmButton())  # Add confirmation button
                    await player.send(intro_msg, embed=char_embed, view=view)
                    await view.wait()
                    if view.selected_skills:
                        for idx, field in enumerate(char_embed.fields):
                            if field.name == f"Skills (Choose {class_data['skills']['choose']})":
                                char_embed.set_field_at(
                                    idx,
                                    name="Skills",
                                    value=", ".join(view.selected_skills),
                                    inline=False
                                )
                                break
                        character["skills"] = view.selected_skills
                    intro_msg = f"Your skills for {character['name']} are set!"
                
                # Handle spells (if applicable)
                if "spells" in class_data:
                    if "choose_cantrips" in class_data["spells"]:
                        char_embed.add_field(
                            name=f"Cantrips (Choose {class_data['spells']['choose_cantrips']})",
                            value=", ".join(class_data["spells"]["cantrips"]),
                            inline=False
                        )
                        view = SelectionView(player_id, 0, selection_type="cantrips", choose_count=class_data["spells"]["choose_cantrips"])
                        view.add_item(SpellsDropdown("Cantrip", class_data["spells"]["cantrips"], class_data["spells"]["choose_cantrips"]))
                        view.add_item(ConfirmButton())  # Add confirmation button
                        await player.send(intro_msg, embed=char_embed, view=view)
                        await view.wait()
                        if view.selected_cantrips:
                            for idx, field in enumerate(char_embed.fields):
                                if field.name == f"Cantrips (Choose {class_data['spells']['choose_cantrips']})":
                                    char_embed.set_field_at(
                                        idx,
                                        name="Cantrips",
                                        value=", ".join(view.selected_cantrips),
                                        inline=False
                                    )
                                    break
                            character["cantrips"] = view.selected_cantrips
                        intro_msg = f"Your cantrips for {character['name']} are set!"
                    
                    if "choose_spells" in class_data["spells"]:
                        char_embed.add_field(
                            name=f"1st-Level Spells (Choose {class_data['spells']['choose_spells']})",
                            value=", ".join(class_data["spells"]["spells"]),
                            inline=False
                        )
                        view = SelectionView(player_id, 0, selection_type="spells", choose_count=class_data["spells"]["choose_spells"])
                        view.add_item(SpellsDropdown("Spell", class_data["spells"]["spells"], class_data["spells"]["choose_spells"]))
                        view.add_item(ConfirmButton())  # Add confirmation button
                        await player.send(intro_msg, embed=char_embed, view=view)
                        await view.wait()
                        if view.selected_spells:
                            for idx, field in enumerate(char_embed.fields):
                                if field.name == f"1st-Level Spells (Choose {class_data['spells']['choose_spells']})":
                                    char_embed.set_field_at(
                                        idx,
                                        name="1st-Level Spells",
                                        value=", ".join(view.selected_spells),
                                        inline=False
                                    )
                                    break
                            character["spells"] = view.selected_spells
                        intro_msg = f"Your spells for {character['name']} are set!"
                
                game["characters"][player_id] = character
                await self.save_game(channel_id, game)
                await player.send(intro_msg, embed=char_embed)
                await ctx.send(f"Player <@{player_id}> completed the special choices for their character.")
                completed_players.add(player_id)
            
            if len(completed_players) == len(game["player_ids"]):
                await ctx.send("Now players use `!start` to begin this adventure!")
            
            await self.add_to_game_history(channel_id, {
                "event": "campaign_theme_set",
                "theme": theme,
                "timestamp": datetime.now().isoformat()
            })
            
        except asyncio.TimeoutError:
            await ctx.send("Campaign setup timed out. Please try again when you're ready.")
    
    @commands.command(name="start")
    async def start_game(self, ctx):
        """Starts the D&D game by creating a private IC channel and OOC thread."""
        channel_id = str(ctx.channel.id)
        game = await self.get_game(channel_id)
        
        if not game:
            await ctx.send("There is no active D&D game in this channel. Use `!dnd` to create one.")
            return
        
        if not game["is_ai_gm"]:
            await ctx.send("This command is only available for games with Emo as the Game Master.")
            return
        
        if game["state"] != "active":
            await ctx.send("The game hasn’t been fully set up yet. Complete the campaign setup with `!campaign_setup` first.")
            return
        
        # Check if all players have completed their choices
        for player_id in game["player_ids"]:
            if player_id not in game["characters"]:
                player = self.bot.get_user(int(player_id))
                player_name = player.display_name if player else f"User {player_id}"
                await ctx.send(f"Player {player_name} hasn’t created a character yet. Use `!creation` or `!random`.")
                return
        
        # Create permission overwrites
        guild = ctx.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
        }
        for player_id in game["player_ids"]:
            player = guild.get_member(int(player_id))
            if player:
                overwrites[player] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        # Create private IC channel
        ic_channel = await guild.create_text_channel(
            name="IC Chat dnd",
            overwrites=overwrites,
            topic=f"In-character chat for the {game['theme']} adventure!"
        )
        
        # Create OOC thread
        ooc_thread = await ic_channel.create_thread(
            name="OOC Chat (D&D)",
            type=discord.ChannelType.public_thread,
            reason="Out-of-character chat for the D&D game"
        )
        
        # Update game data
        game["ic_channel_id"] = str(ic_channel.id)
        game["ooc_thread_id"] = str(ooc_thread.id)
        game["state"] = "started"
        game["last_updated"] = datetime.now().isoformat()
        await self.save_game(channel_id, game)
        
        # Notify in original channel and new IC channel
        await ctx.send(f"The adventure begins! Join the private channel {ic_channel.mention} for in-character play. Use the thread {ooc_thread.mention} for out-of-character chat.")
        await ic_channel.send(f"Welcome to the {game['theme']} adventure, brave heroes! Your journey starts here.")
        await ic_channel.send("use '!emo' to give your game master take control over game in IC Chat")
        await ic_channel.send("`Disclaimer: Only Use Ic Chat For In Game Conversation!!`")
        await ooc_thread.send("This is the OOC thread for side chats and questions!")
        
        await self.add_to_game_history(channel_id, {
            "event": "game_started",
            "ic_channel_id": str(ic_channel.id),
            "ooc_thread_id": str(ooc_thread.id),
            "timestamp": datetime.now().isoformat()
        })

    def cog_unload(self):
        if self.use_mongo:
            self.mongo_client.close()

async def setup(bot):
    await bot.add_cog(DnDGame(bot))