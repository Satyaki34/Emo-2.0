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
        self.view.selected_skills = self.values  # Store selection, but don’t stop the view

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
            self.view.selected_spells = self.values  # Store selection, but don’t stop the view

class SelectionView(ui.View):
    def __init__(self, player_id, inventory_length, timeout=60):
        super().__init__(timeout=timeout)
        self.player_id = player_id
        self.selected_inventory = [None] * inventory_length  # Pre-populate with None for "OR" pairs
        self.selected_skills = None
        self.selected_cantrips = None
        self.selected_spells = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(self.player_id)
    
    async def on_timeout(self):
        self.stop()

class ConfirmButton(ui.Button):
    def __init__(self):
        super().__init__(label="Confirm", style=discord.ButtonStyle.green)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
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
        self.system_prompts = {  # Unchanged system_prompts
            "campaign_creation": """
            You are Emo, an AI Dungeon Master for a text-based D&D campaign.
            Generate a rich, immersive campaign setting based on the theme provided.
            Include:
            - A compelling main plot (string)
            - 3-5 key locations (list of strings)
            - A main antagonist with clear motivations (object with 'name' and 'motivation' fields)
            - 2-3 potential side quests (list of strings)
            - A starting scenario to introduce players to the world (object with 'location' and 'description' fields)

            Format your response **strictly as a JSON object** with these exact keys: 'main_plot', 'locations', 'antagonist', 'side_quests', 'starting_scenario'. 
            Do not include any additional text, explanations, or markdown outside the JSON structure. Return only the raw JSON string.
            Example:
            {
                "main_plot": "A dark force has unleashed a plague of undead upon the land.",
                "locations": ["Ruined City", "Ancient Lab", "Zombie Lair"],
                "antagonist": {"name": "Gragnor", "motivation": "To rule over the living and dead."},
                "side_quests": ["Rescue trapped survivors", "Find the lost cure"],
                "starting_scenario": {"location": "Abandoned Shop", "description": "You huddle inside as groans echo outside."}
            }
            """,
            "narration": """
            You are Emo, an AI Dungeon Master narrating a D&D campaign.
            Create vivid, atmospheric descriptions of the current scene, incorporating:
            - Visual details of the environment
            - Ambient sounds and smells
            - NPCs present and their immediate actions
            - Potential interactions or points of interest
            - Any immediate dangers or opportunities
            
            Keep your narration engaging but concise (2-3 paragraphs).
            """,
            "npc_interaction": """
            You are Emo, an AI Dungeon Master roleplaying as the NPC {npc_name}.
            {npc_name} is a {npc_description}.
            
            Respond to the player's interaction in character, considering:
            - The NPC's personality and goals
            - The current situation and location
            - The NPC's relationship with the players
            - Any relevant plot information the NPC might know
            
            Keep responses natural and conversational.
            """,
            "combat": """
            You are Emo, an AI Dungeon Master managing a D&D combat encounter.
            Current combat state:
            {combat_state}
            
            Narrate the results of the most recent action, including:
            - Description of the attack or action
            - Result of any dice rolls
            - Effects on targets
            - Current battlefield conditions
            - Any changes to the combat situation
            
            Then, prompt the next character in initiative order for their action.
            """,
            "dice_roll": """
            You are Emo, an AI Dungeon Master interpreting a dice roll result.
            
            Roll: {roll_notation} = {roll_result}
            Context: {roll_context}
            
            Describe the outcome of this roll in an engaging way, considering:
            - How close it was to success/failure
            - The difficulty of the task (DC if provided)
            - Any consequences or effects that result
            - How it advances the current scene
            
            Keep your description brief but vivid.
            """
        }
    
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
            return "Sorry, my storytelling brain isn’t working right now. Check if GeminiChat is set up correctly!"
        
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
                    await ctx.send("Emo will be your Game Master! Use `!campaign_setup` to start creating your adventure.")
                else:
                    await ctx.send(f"{gm_name} will be your Game Master! More D&D commands will be available soon.")
                
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
        game = await self.get_game(channel_id)
        if not game:
            await ctx.send("There is no active D&D game in this channel.")
            return
        if str(ctx.author.id) != game["created_by"] and str(ctx.author.id) != game["game_master_id"]:
            await ctx.send("Only the game creator or Game Master can end this game.")
            return
        await self.delete_game(channel_id)
        await ctx.send("The D&D game has been ended. Thanks for playing!")
    
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
            await ctx.send(f"Please make your character first using `!creation`. Players without characters: {missing_str}")
            return
        
        embed = discord.Embed(
            title="📜 Campaign Theme Selection 📜",
            description="Let’s set the tone for your adventure!",
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
                f"Gather 'round, brave souls {player_mentions}! I, Emo, your trusty Game Master, "
                f"welcome you to an epic saga woven in the tapestry of {theme}. Prepare your hearts "
                f"and steel your spirits—our grand tale is about to unfold! When you're ready, brave "
                f"travelers, use `!start` to embark on this wondrous journey."
            )
            
            game["theme"] = theme
            game["state"] = "active"
            game["last_updated"] = datetime.now().isoformat()
            await self.save_game(channel_id, game)
            
            await ctx.send(welcome_msg)
            
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
            
            for player_id in game["player_ids"]:
                character = game["characters"][player_id]
                race_key = race_mapping.get(character["race"].split()[0], character["race"])
                if race_key not in RACES:
                    await ctx.send(f"Error: Invalid race '{character['race']}' for <@{player_id}>.")
                    continue
                
                race_data = RACES[race_key]
                class_data = CLASSES[character["class"]]
                
                # Initial embed with fixed inventory
                intro_msg = (
                    f"Hail, noble <@{player_id}>! Here lies the tale of your character, "
                    f"a legend poised to shape the realm of {theme}!"
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
                    view = SelectionView(player_id, len(choosable_pairs))
                    for i, pair in enumerate(choosable_pairs):
                        options = [opt.strip() for opt in pair.split(" OR ")]
                        view.add_item(InventoryDropdown(options, i))
                    view.add_item(ConfirmButton())
                    await ctx.send(intro_msg, embed=char_embed, view=view)
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
                    intro_msg = f"<@{player_id}>, your inventory is set!"
                    await ctx.send(intro_msg, embed=char_embed)
                else:
                    character["inventory"] = fixed_items
                
                # Handle skills
                if "skills" in class_data and class_data["skills"]["choose"] > 0:
                    char_embed.add_field(
                        name=f"Skills (Choose {class_data['skills']['choose']})",
                        value=", ".join(class_data["skills"]["options"]),
                        inline=False
                    )
                    view = SelectionView(player_id, 0)  # No inventory pairs for skills
                    view.add_item(SkillsDropdown(class_data["skills"]["options"], class_data["skills"]["choose"]))
                    view.add_item(ConfirmButton())  # Add confirmation button
                    await ctx.send(intro_msg, embed=char_embed, view=view)
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
                    intro_msg = f"<@{player_id}>, your skills are set!"
                
                # Handle spells (if applicable)
                if "spells" in class_data:
                    if "choose_cantrips" in class_data["spells"]:
                        char_embed.add_field(
                            name=f"Cantrips (Choose {class_data['spells']['choose_cantrips']})",
                            value=", ".join(class_data["spells"]["cantrips"]),
                            inline=False
                        )
                        view = SelectionView(player_id, 0)
                        view.add_item(SpellsDropdown("Cantrip", class_data["spells"]["cantrips"], class_data["spells"]["choose_cantrips"]))
                        view.add_item(ConfirmButton())  # Add confirmation button
                        await ctx.send(intro_msg, embed=char_embed, view=view)
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
                        intro_msg = f"<@{player_id}>, your cantrips are set!"
                    
                    if "choose_spells" in class_data["spells"]:
                        char_embed.add_field(
                            name=f"1st-Level Spells (Choose {class_data['spells']['choose_spells']})",
                            value=", ".join(class_data["spells"]["spells"]),
                            inline=False
                        )
                        view = SelectionView(player_id, 0)
                        view.add_item(SpellsDropdown("Spell", class_data["spells"]["spells"], class_data["spells"]["choose_spells"]))
                        view.add_item(ConfirmButton())  # Add confirmation button
                        await ctx.send(intro_msg, embed=char_embed, view=view)
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
                        intro_msg = f"<@{player_id}>, your spells are set!"
                
                game["characters"][player_id] = character
                await self.save_game(channel_id, game)
                await ctx.send(intro_msg, embed=char_embed)
            
            await self.add_to_game_history(channel_id, {
                "event": "campaign_theme_set",
                "theme": theme,
                "timestamp": datetime.now().isoformat()
            })
            
        except asyncio.TimeoutError:
            await ctx.send("Campaign setup timed out. Please try again when you're ready.")

    def cog_unload(self):
        if self.use_mongo:
            self.mongo_client.close()

async def setup(bot):
    await bot.add_cog(DnDGame(bot))