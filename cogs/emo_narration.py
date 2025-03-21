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