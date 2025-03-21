import discord
from discord.ext import commands
import asyncio

class EmoNarration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_chat = None
        self.game_histories = {}  # Store chat history per IC channel

    async def setup_gemini_chat(self):
        if not self.gemini_chat:
            self.gemini_chat = self.bot.get_cog('GeminiChat')
            if not self.gemini_chat:
                print("WARNING: GeminiChat cog not found.")
            elif not hasattr(self.gemini_chat, 'model'):
                print("WARNING: GeminiChat cog loaded but has no model attribute.")

    async def get_gemini_response(self, system_prompt, user_prompt, ic_channel_id):
        await self.setup_gemini_chat()
        if not self.gemini_chat or not hasattr(self.gemini_chat, 'model') or not self.gemini_chat.model:
            return "Sorry, my narration brain isn't working! Check if GEMINI_API_KEY is set in .env."
        try:
            # Use existing history or start fresh
            if ic_channel_id not in self.game_histories:
                self.game_histories[ic_channel_id] = []
            
            # Convert history to Gemini format with roles
            history = [{"role": "user" if i % 2 == 0 else "model", "parts": [{"text": entry["content"]}]}
                      for i, entry in enumerate(self.game_histories[ic_channel_id])]
            
            chat = self.gemini_chat.model.start_chat(history=history)
            
            # Send system prompt first
            await asyncio.to_thread(chat.send_message, {"role": "user", "parts": [{"text": system_prompt}]})
            
            # Then send the user prompt and get response
            response = await asyncio.to_thread(chat.send_message, {"role": "user", "parts": [{"text": user_prompt}]})
            narration = response.text
            
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
        players = ", ".join(game["players"])
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

        # Generate narration with simpler style
        system_prompt = "You are Emo, a Dungeon Master for a DnD adventure. Narrate in third-person perspective (e.g., 'Mira tries to reach out'), using simple, clear language. Describe scenes and actions directly, explain dice rolls clearly (e.g., 'roll a d20 and add Persuasion bonus'), and weave in character details (race, class, skills, traits, equipment). Respond to player choices with checks when needed, and keep responses short (up to 7 lines)."
        user_prompt = f"Start a {theme} adventure for players {players} with characters: {'; '.join(character_details)}. Set the scene and begin the story."
        async with ctx.typing():
            narration = await self.get_gemini_response(system_prompt, user_prompt, str(ctx.channel.id))
            await ctx.send(narration)

    @commands.command(name="roll")
    async def roll_dice(self, ctx):
        """Enhanced D&D dice roller with beautiful UI and animated buttons."""
        import random
        from discord import ui, SelectOption

        # Check if game has started and this is the OOC thread
        dnd_game = self.bot.get_cog('DnDGame')
        if not dnd_game:
            await ctx.send("Game setup isn't ready yet.")
            return

        game = None
        channel_id = str(ctx.channel.id)
        for stored_game in (dnd_game.active_games.values() if not dnd_game.use_mongo else dnd_game.games_collection.find()):
            if stored_game.get("ooc_thread_id") == channel_id:
                game = stored_game
                break

        if not game or game.get("state") != "started" or not isinstance(ctx.channel, discord.Thread):
            await ctx.send("You can only use !roll in the OOC thread after the game has started!")
            return

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
                    title=f"✨ {self.author.display_name}'s Mystical Dice Roller ✨",
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
                    
                    # Show total with special formatting
                    total_value = f"**{total}**"
                    if total >= self.die_type and self.die_type > 1:  # Natural max
                        total_value = f"⭐ {total} ⭐ CRITICAL!"
                    elif total == 1 and self.die_type > 1:  # Natural 1
                        total_value = f"☠️ {total} ☠️ FUMBLE!"
                    
                    embed.add_field(name="Total", value=total_value, inline=True)
                    
                    # Add flavor text based on roll result
                    if mode == "Advantage":
                        embed.set_footer(text="The gods smile upon your roll!")
                    elif mode == "Disadvantage":
                        embed.set_footer(text="The fates test your resolve!")
                    else:
                        embed.set_footer(text="May fortune favor the bold!")
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
                    
                    embed.set_footer(text="✨ Crafted by the Arcane Artificers Guild ✨")
                
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

        view = DiceRollerView(ctx.author)
        embed = await view.build_embed()
        view.message = await ctx.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not message.reference:
            return

        # Check if this is a reply to Emo in an IC chat
        dnd_game = self.bot.get_cog('DnDGame')
        if not dnd_game:
            return

        game = None
        for stored_game in (dnd_game.active_games.values() if not dnd_game.use_mongo else dnd_game.games_collection.find()):
            if stored_game.get("ic_channel_id") == str(message.channel.id):
                game = stored_game
                break

        if not game or not game.get("is_ai_gm"):
            return

        # Check if replying to Emo's message
        replied_msg = await message.channel.fetch_message(message.reference.message_id)
        if replied_msg.author != self.bot.user:
            return

        # Continue the story with simpler style
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
        system_prompt = "You are Emo, a Dungeon Master for a DnD adventure. Narrate in third-person perspective (e.g., 'Mira tries to reach out'), using simple, clear language. Describe scenes and actions directly, explain dice rolls clearly (e.g., 'roll a d20 and add Persuasion bonus'), and weave in character details (race, class, skills, traits, equipment). Respond to player choices with checks when needed, and keep responses short (up to 7 lines)."
        user_prompt = f"Continue the {game['theme']} adventure with characters: {'; '.join(character_details)}. Player action: {message.content}"
        async with message.channel.typing():
            narration = await self.get_gemini_response(system_prompt, user_prompt, str(message.channel.id))
            await message.reply(narration)

async def setup(bot):
    await bot.add_cog(EmoNarration(bot))