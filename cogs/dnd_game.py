# cogs/dnd_game.py
import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
import os
import random
import json
from dotenv import load_dotenv
from datetime import datetime

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
                
        self.gemini_model = None  # Changed from gemini_client to gemini_model
        self.system_prompts = {
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
        """Set up the Gemini model by getting it from the GeminiChat cog"""
        if not self.gemini_model:
            gemini_cog = self.bot.get_cog('GeminiChat')
            if gemini_cog and hasattr(gemini_cog, 'model'):
                self.gemini_model = gemini_cog.model
                print("Successfully connected to Gemini model for DnD features")
            else:
                print("WARNING: GeminiChat cog not found or has no 'model' attribute.")
    
    async def get_gemini_response(self, system_prompt, user_prompt, history=None):
        """Get a response from Gemini using the chat-based API"""
        await self.setup_gemini_model()
        if not self.gemini_model:
            return "Sorry, my storytelling brain isn’t working right now. Check if GeminiChat is set up correctly!"
        
        try:
            # Start a new chat session for each request (no persistent history across calls)
            chat = self.gemini_model.start_chat(history=[])
            # Send the system prompt first
            await asyncio.to_thread(chat.send_message, system_prompt)
            # Then send the user prompt
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
            await ctx.send("Only the game creator or Game Master(DM) can set up the campaign.")
            return
        
        # New: Check if all players have created characters
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
        
        # Proceed with campaign setup if all players have characters
        embed = discord.Embed(
            title="📜 Campaign Setup 📜",
            description="Let’s create your D&D campaign! I’ll generate a campaign based on your theme.",
            color=discord.Color.dark_gold()
        )
        embed.add_field(
            name="Instructions",
            value="Please provide a theme for the campaign (e.g., 'zombie apocalypse in a magical city', 'pirate adventure on cursed seas')."
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
            
            await ctx.send("Generating your campaign... please wait.")
            campaign_prompt = f"Generate a campaign based on the theme: '{theme}'"
            campaign_response = await self.get_gemini_response(
                self.system_prompts["campaign_creation"],
                campaign_prompt
            )
            
            try:
                campaign_data = json.loads(campaign_response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', campaign_response, re.DOTALL)
                if json_match:
                    try:
                        campaign_data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        await ctx.send("Error: Failed to extract valid JSON from AI response.")
                        print(f"Invalid JSON response: {campaign_response}")
                        return
                else:
                    await ctx.send("Error: Failed to parse campaign data from AI response.")
                    print(f"Invalid JSON response: {campaign_response}")
                    return
            
            required_fields = ["main_plot", "locations", "antagonist", "side_quests", "starting_scenario"]
            if not all(field in campaign_data for field in required_fields):
                await ctx.send("Error: Campaign generation failed to include all required elements.")
                print(f"Missing fields in response: {campaign_response}")
                return
            
            campaign_data["name"] = f"Campaign: {theme.capitalize()}"
            game["campaign"] = campaign_data
            game["state"] = "active"
            game["last_updated"] = datetime.now().isoformat()
            game["current_scene"] = {
                "name": campaign_data["starting_scenario"].get("location", "Starting Location"),
                "description": campaign_data["starting_scenario"].get("description", "The adventure begins...")
            }
            await self.save_game(channel_id, game)
            
            narration_response = await self.get_gemini_response(
                self.system_prompts["narration"],
                f"Narrate the starting scenario: {campaign_data['starting_scenario']['description']}"
            )
            
            summary_embed = discord.Embed(
                title=f"🎉 Campaign Created: {campaign_data['name']} 🎉",
                description="Your adventure is ready to begin!",
                color=discord.Color.green()
            )
            summary_embed.add_field(name="Main Plot", value=campaign_data["main_plot"], inline=False)
            summary_embed.add_field(name="Key Locations", value="\n".join(campaign_data["locations"]), inline=False)
            summary_embed.add_field(name="Antagonist", value=f"{campaign_data['antagonist']['name']} - {campaign_data['antagonist']['motivation']}", inline=False)
            summary_embed.add_field(name="Side Quests", value="\n".join(campaign_data["side_quests"]), inline=False)
            summary_embed.add_field(name="Starting Scenario", value=campaign_data["starting_scenario"]["description"], inline=False)
            summary_embed.add_field(name="Scene Narration", value=narration_response[:1024], inline=False)
            
            if len(narration_response) > 1024:
                narration_parts = [narration_response[i:i+1024] for i in range(1024, len(narration_response), 1024)]
                for i, part in enumerate(narration_parts, 1):
                    summary_embed.add_field(name=f"Scene Narration (Part {i+1})", value=part, inline=False)
            
            await ctx.send(embed=summary_embed)
            
            await self.add_to_game_history(channel_id, {
                "event": "campaign_setup",
                "theme": theme,
                "campaign_name": campaign_data["name"],
                "timestamp": datetime.now().isoformat()
            })
            
            await ctx.send("The adventure begins! What would you like to do next?")
            
        except asyncio.TimeoutError:
            await ctx.send("Campaign setup timed out. Please try again when you're ready.")
    
    def cog_unload(self):
        if self.use_mongo:
            self.mongo_client.close()

async def setup(bot):
    await bot.add_cog(DnDGame(bot))