import discord
from discord.ext import commands
import asyncio
import json
import random
import os
import time
import re

class EmoNarration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_chat = None
        self.game_histories = {}  # Store chat history per IC channel
        self.pending_actions = {}  # Store pending actions (e.g., dice rolls) per IC channel
        self.world_details = {}    # Store world building elements
        self.scene_descriptions = {}  # Store current scene descriptions
        self.npc_database = {}     # Store NPCs the party has encountered
        
        # Path for storing persistent data
        self.data_folder = "./data/narration"
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Load previous data if available
        self.load_persistent_data()

    def load_persistent_data(self):
        """Load persistent storytelling data from files."""
        try:
            world_path = os.path.join(self.data_folder, "world_details.json")
            if os.path.exists(world_path):
                with open(world_path, 'r') as f:
                    self.world_details = json.load(f)
                    
            npc_path = os.path.join(self.data_folder, "npc_database.json")
            if os.path.exists(npc_path):
                with open(npc_path, 'r') as f:
                    self.npc_database = json.load(f)
                    
            scenes_path = os.path.join(self.data_folder, "scene_descriptions.json")
            if os.path.exists(scenes_path):
                with open(scenes_path, 'r') as f:
                    self.scene_descriptions = json.load(f)
        except Exception as e:
            print(f"Error loading narration data: {e}")

    def save_persistent_data(self):
        """Save storytelling data to persist between bot restarts."""
        try:
            with open(os.path.join(self.data_folder, "world_details.json"), 'w') as f:
                json.dump(self.world_details, f)
                
            with open(os.path.join(self.data_folder, "npc_database.json"), 'w') as f:
                json.dump(self.npc_database, f)
                
            with open(os.path.join(self.data_folder, "scene_descriptions.json"), 'w') as f:
                json.dump(self.scene_descriptions, f)
        except Exception as e:
            print(f"Error saving narration data: {e}")

    async def setup_gemini_chat(self):
        if not self.gemini_chat:
            self.gemini_chat = self.bot.get_cog('GeminiChat')
            if not self.gemini_chat:
                print("WARNING: GeminiChat cog not found.")
            elif not hasattr(self.gemini_chat, 'model'):
                print("WARNING: GeminiChat cog loaded but has no model attribute.")

    async def save_pending_action(self, ic_channel_id, action_data):
        dnd_game = self.bot.get_cog('DnDGame')
        if dnd_game and dnd_game.use_mongo:
            await dnd_game.save_game(ic_channel_id, {"pending_actions": self.pending_actions.get(ic_channel_id, {})})
        # Always update in-memory regardless of MongoDB
        if ic_channel_id not in self.pending_actions:
            self.pending_actions[ic_channel_id] = {}
        self.pending_actions[ic_channel_id].update(action_data)

    async def extract_narrative_elements(self, narration, ic_channel_id):
        """Extract world building elements from the narration to maintain consistency."""
        # Simple extraction of location descriptions
        if "SCENE:" in narration:
            scene_match = re.search(r"SCENE: (.+?)(?=\n|$)", narration)
            if scene_match:
                self.scene_descriptions[ic_channel_id] = scene_match.group(1)
                narration = narration.replace(scene_match.group(0), "")
                
        # Extract NPC introductions
        if "NPC:" in narration:
            npc_matches = re.findall(r"NPC: ([^:]+): (.+?)(?=\n|$)", narration)
            if npc_matches:
                if ic_channel_id not in self.npc_database:
                    self.npc_database[ic_channel_id] = {}
                    
                for npc_name, npc_desc in npc_matches:
                    self.npc_database[ic_channel_id][npc_name.strip()] = npc_desc.strip()
                    narration = narration.replace(f"NPC: {npc_name}: {npc_desc}", "")
                
        # Save updated data
        self.save_persistent_data()
        return narration.strip()

    async def get_gemini_response(self, system_prompt, user_prompt, ic_channel_id):
        await self.setup_gemini_chat()
        if not self.gemini_chat or not hasattr(self.gemini_chat, 'model') or not self.gemini_chat.model:
            return "Sorry, my narration brain isn't working! Check if GEMINI_API_KEY is set in .env."
        try:
            # Use existing history or start fresh
            if ic_channel_id not in self.game_histories:
                self.game_histories[ic_channel_id] = []
            
            # Load pending actions from MongoDB if available
            dnd_game = self.bot.get_cog('DnDGame')
            if dnd_game and dnd_game.use_mongo:
                game = await dnd_game.get_game(ic_channel_id)
                if game and "pending_actions" in game:
                    self.pending_actions[ic_channel_id] = game["pending_actions"]
            
            # Convert history to Gemini format with roles
            history = [{"role": "user" if i % 2 == 0 else "model", "parts": [{"text": entry["content"]}]}
                      for i, entry in enumerate(self.game_histories[ic_channel_id])]
            
            # Add context from saved world details
            context_info = []
            
            # Add current scene
            if ic_channel_id in self.scene_descriptions:
                context_info.append(f"Current scene: {self.scene_descriptions[ic_channel_id]}")
                
            # Add NPCs the party has met
            if ic_channel_id in self.npc_database and self.npc_database[ic_channel_id]:
                npc_info = "\nNPCs the party has encountered:\n"
                for name, desc in self.npc_database[ic_channel_id].items():
                    npc_info += f"- {name}: {desc}\n"
                context_info.append(npc_info)
                
            # Add general world details
            if ic_channel_id in self.world_details:
                context_info.append(f"World details: {self.world_details[ic_channel_id]}")
                
            # Add context to user prompt
            if context_info:
                context_str = "\n\nContext (not to be repeated verbatim):\n" + "\n".join(context_info)
                user_prompt += context_str
            
            # Append pending actions to user_prompt for context
            pending = self.pending_actions.get(ic_channel_id, {})
            if pending:
                pending_str = "; ".join([f"{char}: {action}" for char, action in pending.items()])
                user_prompt += f"\nPending actions: {pending_str}"
            
            chat = self.gemini_chat.model.start_chat(history=history)
            
            # Send system prompt first
            await asyncio.to_thread(chat.send_message, {"role": "user", "parts": [{"text": system_prompt}]})
            
            # Then send the user prompt and get response
            response = await asyncio.to_thread(chat.send_message, {"role": "user", "parts": [{"text": user_prompt}]})
            narration = response.text
            
            # Extract and save narrative elements for future context
            narration = await self.extract_narrative_elements(narration, ic_channel_id)
            
            # Update history - add only the actual user prompt and model response
            self.game_histories[ic_channel_id].append({"role": "user", "content": user_prompt})
            self.game_histories[ic_channel_id].append({"role": "model", "content": narration})
            
            return narration
        except Exception as e:
            print(f"Error getting Gemini response: {e}")
            return "Sorry, something went wrong with the narration!"

    @commands.command(name="emo")
    async def emo_narrate(self, ctx):
        dnd_game = self.bot.get_cog('DnDGame')
        if not dnd_game:
            await ctx.send("Game setup isn't ready yet.")
            return

        # Find the game associated with this channel as IC chat
        game = None
        for stored_game in (dnd_game.active_games.values() if not dnd_game.use_mongo else dnd_game.games_collection.find()):
            if stored_game.get("ic_channel_id") == str(ctx.channel.id):
                game = stored_game
                break

        if not game or not game.get("is_ai_gm"):
            await ctx.send("This command only works in the IC chat with Emo as GM!")
            return

        # Get player info, theme, and detailed character data
        character_names = [game["characters"][pid].get("name", "Unknown") for pid in game["player_ids"]]
        players = ", ".join(character_names)
        theme = game["theme"]
        character_details = []
        for pid in game["player_ids"]:
            char = game["characters"][pid]
            name = char.get("name", "Unknown")
            race = char.get("race", "Unknown")
            char_class = char.get("class", "Unknown")
            spells = ", ".join(char.get("spells", [])) or "None"
            skills = ", ".join(char.get("skills", [])) or "None"
            traits = ", ".join(char.get("traits", [])) or "None"
            equipment = ", ".join(char.get("equipment", [])) or "None"
            character_details.append(f"{name} (Race: {race}, Class: {char_class}, Spells: {spells}, Skills: {skills}, Traits: {traits}, Equipment: {equipment})")

        # Set up embed for "Emo is thinking..." message
        thinking_embed = discord.Embed(
            title="🧠 Emo is crafting your adventure...",
            description="Your story is being woven together...",
            color=0x9370DB  # Medium Purple
        )
        thinking_embed.set_footer(text="Please wait while the magical world takes shape")
        
        thinking_message = await ctx.send(embed=thinking_embed)

        # Improved storytelling system prompt
        system_prompt = """You are Emo, a skilled and engaging Dungeon Master for a D&D adventure. Follow these storytelling guidelines:

1. Begin with a brief, vivid scene description (2-3 lines) that helps players visualize where they are
2. Use simple, everyday language that beginners can easily understand
3. Introduce characters naturally, mentioning one interesting visual detail about each
4. Present clear choices or opportunities for players without overwhelming them
5. Only ask for dice rolls when truly necessary (major challenges, combat, or risky actions)
6. When describing actions, focus on what players see, hear, and feel
7. Create a sense of wonder and adventure appropriate for the theme
8. Include occasional NPC interactions with distinct personalities
9. Gently remind players of their character abilities when relevant
10. Keep your narration under 7 lines for good pacing

Special tags (these won't appear in the final text):
- Use SCENE: tag to mark important location descriptions
- Use NPC: Name: Description to track important non-player characters
- If a dice roll is needed, include PENDING_ROLL: [character] must roll [dice] + [modifier] and explain why in everyday terms
"""

        # First-time adventure start with beginner-friendly approach
        user_prompt = f"Start a {theme} adventure for players {players} with characters: {'; '.join(character_details)}. Create a beginner-friendly opening scene that introduces a simple goal or quest. Tag the scene description with SCENE: and any NPCs with NPC: tags. Use everyday language a new player would understand."
        
        async with ctx.typing():
            narration = await self.get_gemini_response(system_prompt, user_prompt, str(ctx.channel.id))
            
            # Create an engaging message with the narration
            adventure_embed = discord.Embed(
                title=f"🎭 {theme} Adventure Begins!",
                description=narration,
                color=0x1E90FF  # Dodger Blue
            )
            adventure_embed.set_footer(text="Reply to this message to interact with the world")
            
            # Delete the thinking message and send the adventure
            await thinking_message.delete()
            await ctx.send(embed=adventure_embed)

    @commands.command(name="help_emo")
    async def help_emo(self, ctx):
        """Provides beginner-friendly help for playing with Emo."""
        help_embed = discord.Embed(
            title="🧙‍♂️ How to Play with Emo - The Beginner's Guide",
            description="Welcome to your D&D adventure! Here's how to play with Emo, your friendly Dungeon Master.",
            color=0x4CAF50
        )
        
        help_embed.add_field(
            name="📜 To Start An Adventure",
            value="Type `!emo` in your game channel to begin a new adventure.",
            inline=False
        )
        
        help_embed.add_field(
            name="🗣️ Talking and Acting",
            value="Reply to Emo's messages to speak or take actions. Describe what your character wants to do in simple terms, like:\n• \"I walk up to the innkeeper and ask about rumors\"\n• \"I search the room for hidden doors\"\n• \"I cast Light on my staff to brighten the cave\"",
            inline=False
        )
        
        help_embed.add_field(
            name="🎲 Rolling Dice",
            value="When Emo asks for a roll, use `!roll` in the OOC thread. Choose your dice and modifiers from the menu that appears.",
            inline=False
        )
        
        help_embed.add_field(
            name="💡 Tips For Beginners",
            value="• Be specific about what you want to do\n• You don't need to use game terms - just describe actions normally\n• Work together with other players\n• Ask questions if you're confused - Emo is here to help\n• Have fun and be creative!",
            inline=False
        )
        
        await ctx.send(embed=help_embed)

    @commands.command(name="roll")
    async def roll_dice(self, ctx):
        """Enhanced D&D dice roller with beautiful UI and animated buttons."""
        import random
        from discord import ui, SelectOption

        # Check if game has started and this is the OOC thread
        dnd_game = self.bot.get_cog('DnDGame')
        if not dnd_game:
            try:
                await ctx.send("Game setup isn't ready yet.")
            except Exception as e:
                print(f"Error sending message in roll_dice (no DnDGame): {e}")
            return

        game = None
        channel_id = str(ctx.channel.id)
        for stored_game in (dnd_game.active_games.values() if not dnd_game.use_mongo else dnd_game.games_collection.find()):
            if stored_game.get("ooc_thread_id") == channel_id:
                game = stored_game
                break

        print(f"roll_dice: Game found: {game is not None}, State: {game.get('state') if game else 'None'}, Is thread: {isinstance(ctx.channel, discord.Thread)}")
        if not game or game.get("state") != "started" or not isinstance(ctx.channel, discord.Thread):
            try:
                await ctx.send("You can only use !roll in the OOC thread after the game has started!")
            except Exception as e:
                print(f"Error sending message in roll_dice (validation failed): {e}")
            return

        print("roll_dice: Setting up DiceRollerView")
        class DiceRollerView(ui.View):
            def __init__(self, author):
                super().__init__(timeout=120)  # Extended timeout for better UX
                self.author = author
                self.die_type = 20
                self.num_dice = 1
                self.modifier = 0
                self.message = None
                self.dice_image = "https://media.discordapp.net/attachments/1195744344989249646/1352656420205629490/New_dice.png?ex=67decef5&is=67dd7d75&hm=784cb0b94dd2ba8eb0629cc30f30a9516e9706642c44cb4ed5c144e4ad17f36c&=&format=webp&quality=lossless&width=649&height=694"

                # Add select menus with custom placeholders
                self.add_item(self.DiceTypeSelect(self))
                self.add_item(self.NumDiceSelect(self))
                self.add_item(self.ModifierSelect(self))
                
                # Create styled buttons
                self.advantage_button = ui.Button(
                    label="Advantage", 
                    style=discord.ButtonStyle.green, 
                    custom_id="advantage",
                    emoji="⬆️"
                )
                self.advantage_button.callback = self.roll_advantage
                self.add_item(self.advantage_button)
                
                self.roll_button = ui.Button(
                    label="Roll", 
                    style=discord.ButtonStyle.blurple, 
                    custom_id="normal",
                    emoji="🎲"
                )
                self.roll_button.callback = self.roll_normal
                self.add_item(self.roll_button)
                
                self.disadvantage_button = ui.Button(
                    label="Disadvantage", 
                    style=discord.ButtonStyle.red, 
                    custom_id="disadvantage",
                    emoji="⬇️"
                )
                self.disadvantage_button.callback = self.roll_disadvantage
                self.add_item(self.disadvantage_button)
                
                # Add a help button to explain dice rolling concepts
                self.help_button = ui.Button(
                    label="Help", 
                    style=discord.ButtonStyle.secondary, 
                    custom_id="help",
                    emoji="❓"
                )
                self.help_button.callback = self.show_help
                self.add_item(self.help_button)

            class DiceTypeSelect(ui.Select):
                def __init__(self, parent):
                    self.parent = parent
                    options = [
                        SelectOption(label="d4", emoji="🔺", value="4", description="Four-sided die"),
                        SelectOption(label="d6", emoji="🎲", value="6", description="Six-sided die"),
                        SelectOption(label="d8", emoji="🔶", value="8", description="Eight-sided die"),
                        SelectOption(label="d10", emoji="🔷", value="10", description="Ten-sided die"),
                        SelectOption(label="d12", emoji="🔳", value="12", description="Twelve-sided die"),
                        SelectOption(label="d20", emoji="🔴", value="20", default=True, description="Twenty-sided die"),
                        SelectOption(label="d100", emoji="💯", value="100", description="Percentile die")
                    ]
                    super().__init__(placeholder="✨ Choose Die Type ✨", options=options, custom_id="dice_type")

                async def callback(self, interaction):
                    self.parent.die_type = int(self.values[0])
                    # Update embed to reflect the new selection
                    embed = await self.parent.build_embed()
                    await interaction.response.edit_message(embed=embed, view=self.parent)

            class NumDiceSelect(ui.Select):
                def __init__(self, parent):
                    self.parent = parent
                    options = [
                        SelectOption(label=str(i), value=str(i), default=i==1, 
                                    description=f"Roll {i} {'die' if i==1 else 'dice'}")
                        for i in range(1, 11)  # Extended to 10 dice
                    ]
                    super().__init__(placeholder="🎲 Number of Dice 🎲", options=options, custom_id="num_dice")

                async def callback(self, interaction):
                    self.parent.num_dice = int(self.values[0])
                    # Update embed to reflect the new selection
                    embed = await self.parent.build_embed()
                    await interaction.response.edit_message(embed=embed, view=self.parent)

            class ModifierSelect(ui.Select):
                def __init__(self, parent):
                    self.parent = parent
                    options = [
                        SelectOption(
                            label=f"{i:+d}", 
                            value=str(i), 
                            default=i==0,
                            description=f"Add {i} to roll result" if i > 0 else 
                                      ("No modifier" if i == 0 else f"Subtract {abs(i)} from roll result")
                        ) 
                        for i in range(-10, 11)  # Extended range from -10 to +10
                    ]
                    super().__init__(placeholder="🔢 Modifier 🔢", options=options, custom_id="modifier")

                async def callback(self, interaction):
                    self.parent.modifier = int(self.values[0])
                    # Update embed to reflect the new selection
                    embed = await self.parent.build_embed()
                    await interaction.response.edit_message(embed=embed, view=self.parent)

            async def interaction_check(self, interaction):
                # Only the command initiator can use this view
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("This dice roller belongs to someone else!", ephemeral=True)
                    return False
                return True

            async def show_help(self, interaction):
                """Show a helpful explanation of dice rolling concepts for beginners."""
                help_embed = discord.Embed(
                    title="🎲 Dice Rolling Guide for Beginners",
                    description="Here's a quick guide to understanding dice rolls in D&D!",
                    color=0xFFA500  # Orange
                )
                
                help_embed.add_field(
                    name="📊 Dice Types",
                    value=(
                        "• **d4, d6, d8, d10, d12, d20, d100**: Dice with different numbers of sides\n"
                        "• **d20**: Most common for skill checks, attacks, and saving throws\n"
                        "• **d6, d8, d10, d12**: Usually for damage rolls\n"
                        "• **d100**: Used for percentages and random tables"
                    ),
                    inline=False
                )
                
                help_embed.add_field(
                    name="➕ Modifiers",
                    value=(
                        "• **Modifier**: A number you add to or subtract from the dice roll\n"
                        "• Example: If you have +3 Strength, you add 3 to Strength-based rolls"
                    ),
                    inline=False
                )
                
                help_embed.add_field(
                    name="🔄 Advantage & Disadvantage",
                    value=(
                        "• **Advantage**: Roll two d20s and take the **higher** result\n"
                        "• **Disadvantage**: Roll two d20s and take the **lower** result\n"
                        "• These only apply to d20 rolls!"
                    ),
                    inline=False
                )
                
                help_embed.add_field(
                    name="💡 Examples",
                    value=(
                        "• \"Roll a d20+5 for Persuasion\" means roll a 20-sided die and add 5\n"
                        "• \"2d6+3 damage\" means roll two 6-sided dice, add them up, then add 3\n"
                        "• \"Roll with advantage\" means roll 2d20 and use the higher number"
                    ),
                    inline=False
                )
                
                await interaction.response.send_message(embed=help_embed, ephemeral=True)

            async def build_embed(self, rolls=None, total=None, mode=None):
                # Determine color based on die type
                die_colors = {
                    4: 0x00FF00,   # Green
                    6: 0xFFFF00,   # Yellow
                    8: 0xFF9900,   # Orange
                    10: 0x0099FF,  # Light Blue
                    12: 0x9900FF,  # Purple
                    20: 0xFF0000,  # Red
                    100: 0xFFFFFF  # White
                }
                color = die_colors.get(self.die_type, 0xFFD700)  # Gold default
                
                embed = discord.Embed(
                    title=f"✨ {self.author.display_name}'s Dice Roller ✨",
                    description=f"The fate of your adventure hangs in the balance...",
                    color=color
                )
                
                # Set the custom dice image
                embed.set_thumbnail(url=self.dice_image)
                
                # Dice emojis for better visual cues
                dice_emojis = {4: "🔺", 6: "🎲", 8: "🔶", 10: "🔷", 12: "🔳", 20: "🔴", 100: "💯"}
                emoji = dice_emojis.get(self.die_type, "🎲")
                
                if rolls:
                    # Show detailed roll results with emoji
                    rolls_str = ", ".join(f"**{r}**" for r in rolls)
                    
                    # Format title based on roll type
                    roll_title = f"{emoji} Roll Results"
                    if mode:
                        roll_title += f" ({mode})"
                    
                    embed.add_field(
                        name=roll_title, 
                        value=f"{emoji} [{rolls_str}] {emoji}", 
                        inline=False
                    )
                    
                    # Add calculation breakdown
                    calculation = f"Sum: {sum(rolls)}"
                    if self.modifier != 0:
                        calculation += f" {'+' if self.modifier > 0 else ''}{self.modifier} (modifier)"
                    
                    embed.add_field(name="Calculation", value=calculation, inline=True)
                    
                    # Add beginner-friendly explanations of the roll
                    roll_explanation = ""
                    if self.die_type == 20:
                        if total >= 20:
                            roll_explanation = "Critical hit! This is an extremely good roll!"
                        elif total >= 15:
                            roll_explanation = "Great roll! This will succeed at most tasks."
                        elif total >= 10:
                            roll_explanation = "Average roll. May succeed at medium difficulty tasks."
                        else:
                            roll_explanation = "Low roll. Difficult tasks will likely fail."
                    
                    # Show total with special formatting
                    total_value = f"**{total}**"
                    if total >= self.die_type and self.die_type > 1:  # Natural max
                        total_value = f"⭐ {total} ⭐ CRITICAL SUCCESS!"
                    elif total == 1 and self.die_type > 1:  # Natural 1
                        total_value = f"☠️ {total} ☠️ CRITICAL FAILURE!"
                    
                    embed.add_field(name="Total", value=total_value, inline=True)
                    
                    if roll_explanation:
                        embed.add_field(name="What Does This Mean?", value=roll_explanation, inline=False)
                    
                    # Add flavor text based on roll result
                    if mode == "Advantage":
                        embed.set_footer(text="With advantage: rolling twice and taking the higher result!")
                    elif mode == "Disadvantage":
                        embed.set_footer(text="With disadvantage: rolling twice and taking the lower result!")
                    else:
                        embed.set_footer(text="Copy this number when Emo asks for your roll result!")
                else:
                    # Current setup display
                    setup_str = f"{self.num_dice}d{self.die_type}"
                    if self.modifier != 0:
                        setup_str += f" {'+' if self.modifier > 0 else ''}{self.modifier}"
                    
                    embed.add_field(
                        name="🎮 Current Setup",
                        value=f"{emoji} **{setup_str}** {emoji}",
                        inline=False
                    )
                    
                    # Instructions with emoji
                    embed.add_field(
                        name="📝 Instructions",
                        value="1. Select options from the dropdowns\n2. Click a button to roll the dice!",
                        inline=False
                    )
                    
                    # Add explanations
                    embed.add_field(
                        name="⬆️ Advantage",
                        value="Roll 2d20, take highest",
                        inline=True
                    )
                    embed.add_field(
                        name="🎲 Normal Roll",
                        value=f"Roll {self.num_dice}d{self.die_type}",
                        inline=True
                    )
                    embed.add_field(
                        name="⬇️ Disadvantage",
                        value="Roll 2d20, take lowest",
                        inline=True
                    )
                    
                    embed.set_footer(text="Click the ❓ Help button if you're confused about dice rolling")
                
                return embed

            async def roll_advantage(self, interaction):
                # Only valid for d20 rolls
                if self.die_type != 20:
                    await interaction.response.send_message(
                        "Advantage/Disadvantage only works with d20 rolls! Changing to d20...",
                        ephemeral=True
                    )
                    self.die_type = 20
                
                rolls = [random.randint(1, 20) for _ in range(2)]
                total = max(rolls) + self.modifier
                embed = await self.build_embed(rolls, total, "Advantage")
                await interaction.response.edit_message(embed=embed, view=None)
                self.stop()

            async def roll_normal(self, interaction):
                rolls = [random.randint(1, self.die_type) for _ in range(self.num_dice)]
                total = sum(rolls) + self.modifier
                embed = await self.build_embed(rolls, total)
                await interaction.response.edit_message(embed=embed, view=None)
                self.stop()

            async def roll_disadvantage(self, interaction):
                # Only valid for d20 rolls
                if self.die_type != 20:
                    await interaction.response.send_message(
                        "Advantage/Disadvantage only works with d20 rolls! Changing to d20...",
                        ephemeral=True
                    )
                    self.die_type = 20
                
                rolls = [random.randint(1, 20) for _ in range(2)]
                total = min(rolls) + self.modifier
                embed = await self.build_embed(rolls, total, "Disadvantage")
                await interaction.response.edit_message(embed=embed, view=None)
                self.stop()

        print("roll_dice: Sending DiceRollerView")
        view = DiceRollerView(ctx.author)
        embed = await view.build_embed()
        try:
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error sending initial DiceRollerView: {e}")
            await ctx.send("Something went wrong with the dice roller! Check bot permissions or try again.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not message.reference:
            return

        # Check if this is a reply to Emo in an IC chat
        dnd_game = self.bot.get_cog('DnDGame')
        if not dnd_game:
            return

        game = None
        ic_channel_id = str(message.channel.id)
        for stored_game in (dnd_game.active_games.values() if not dnd_game.use_mongo else dnd_game.games_collection.find()):
            if stored_game.get("ic_channel_id") == ic_channel_id:
                game = stored_game
                break

        if not game or not game.get("is_ai_gm"):
            return

        # Check if replying to Emo's message
        replied_msg = await message.channel.fetch_message(message.reference.message_id)
        if replied_msg.author != self.bot.user:
            return

        # Identify the acting character
        player_id = str(message.author.id)
        acting_char = None
        for pid, char in game["characters"].items():
            if pid == player_id:
                acting_char = char.get("name", "Unknown")
                break
        if not acting_char:
            await message.reply("I don’t recognize you in this game!")
            return

        character_names = [game["characters"][pid].get("name", "Unknown") for pid in game["player_ids"]]
        players = ", ".join(character_names)
        character_details = []
        for pid in game["player_ids"]:
            char = game["characters"][pid]
            name = char.get("name", "Unknown")
            race = char.get("race", "Unknown")
            char_class = char.get("class", "Unknown")
            spells = ", ".join(char.get("spells", [])) or "None"
            skills = ", ".join(char.get("skills", [])) or "None"
            traits = ", ".join(char.get("traits", [])) or "None"
            equipment = ", ".join(char.get("equipment", [])) or "None"
            character_details.append(f"{name} (Race: {race}, Class: {char_class}, Spells: {spells}, Skills: {skills}, Traits: {traits}, Equipment: {equipment})")
    
        system_prompt = """You are Emo, a skilled and engaging Dungeon Master for a D&D adventure. Follow these storytelling guidelines:
1. Begin with a brief, vivid scene description (2-3 lines) that helps players visualize where they are
2. Use simple, everyday language that beginners can easily understand
3. Introduce characters naturally, mentioning one interesting visual detail about each
4. Present clear choices or opportunities for players without overwhelming them
5. Only ask for dice rolls when truly necessary (major challenges, combat, or risky actions)
6. When describing actions, focus on what players see, hear, and feel
7. Create a sense of wonder and adventure appropriate for the theme
8. Include occasional NPC interactions with distinct personalities
9. Gently remind players of their character abilities when relevant
10. Keep your narration under 7 lines for good pacing

Special tags (these won't appear in the final text):
- Use SCENE: tag to mark important location descriptions
- Use NPC: Name: Description to track important non-player characters
- If a dice roll is needed, include PENDING_ROLL: [character] must roll [dice] + [modifier] and explain why in everyday terms
"""
    
        # Check pending actions for this character with better error handling
        pending = self.pending_actions.get(ic_channel_id, {})
        pending_for_char = pending.get(acting_char) if acting_char in pending else None
        narration = ""
    
        try:
            if pending_for_char and message.content.strip().isdigit():
                # Handle roll result
                roll_result = int(message.content.strip())
                user_prompt = f"Continue the {game['theme']} adventure for players {players} with characters: {'; '.join(character_details)}. {acting_char} rolled {roll_result} for {pending_for_char}."
                async with message.channel.typing():
                    narration = await self.get_gemini_response(system_prompt, user_prompt, ic_channel_id)
                if acting_char in self.pending_actions.get(ic_channel_id, {}):
                    del self.pending_actions[ic_channel_id][acting_char]
                if ic_channel_id in self.pending_actions and not self.pending_actions[ic_channel_id]:
                    del self.pending_actions[ic_channel_id]
                await self.save_pending_action(ic_channel_id, {})
            else:
                # Process new action
                user_prompt = f"Continue the {game['theme']} adventure for players {players} with characters: {'; '.join(character_details)}. Player action by {acting_char}: {message.content}"
                async with message.channel.typing():
                    narration = await self.get_gemini_response(system_prompt, user_prompt, ic_channel_id)
    
            # Parse narration for HP and EXP changes
            if dnd_game:
                hp_match = re.search(r"(\w+) takes (\d+) damage", narration, re.IGNORECASE)
                if hp_match:
                    char_name, damage = hp_match.groups()
                    if char_name == acting_char:
                        await dnd_game.update_character_stats(ic_channel_id, player_id, -int(damage))
                        narration += f"\n{acting_char}'s HP decreased by {damage}!"

                heal_match = re.search(r"(\w+) heals for (\d+)", narration, re.IGNORECASE)
                if heal_match:
                    char_name, healing = heal_match.groups()
                    if char_name == acting_char:
                        await dnd_game.update_character_stats(ic_channel_id, player_id, int(healing))
                        narration += f"\n{acting_char}'s HP increased by {healing}!"

                exp_match = re.search(r"(\w+) gains (\d+) EXP", narration, re.IGNORECASE)
                if exp_match:
                    char_name, exp = exp_match.groups()
                    if char_name == acting_char:
                        await dnd_game.award_exp(ic_channel_id, player_id, int(exp))
                        narration += f"\n{acting_char} gained {exp} EXP!"

            # Check for new pending rolls in narration
            if "PENDING_ROLL:" in narration:
                match = re.search(r"PENDING_ROLL: (\w+) must roll (.+)", narration)
                if match:
                    char_name, roll = match.groups()
                    await self.save_pending_action(ic_channel_id, {char_name: f"roll {roll}"})
                    narration = narration.replace(match.group(0), f"{char_name}, please roll {roll} in your next reply.")

            # Add reminders for other pending actions
            if ic_channel_id in self.pending_actions:
                reminders = [f"{char}, your roll for {action} is still pending!"
                            for char, action in self.pending_actions[ic_channel_id].items() if char != acting_char]
                if reminders:
                    narration += "\n" + "\n".join(reminders)

            # Send narration as an embed
            adventure_embed = discord.Embed(
                title=f"🎭 {game['theme']} Adventure Continues",
                description=narration,
                color=0x1E90FF  # Dodger Blue
            )
            adventure_embed.set_footer(text="Reply to this message to interact with the world")
            await message.reply(embed=adventure_embed)

        except Exception as e:
            error_msg = f"An error occurred while processing your action: {str(e)}"
            await message.reply(error_msg)
            print(f"Error in on_message for character {acting_char}: {str(e)}")

async def setup(bot):
    await bot.add_cog(EmoNarration(bot))