import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import re
import os
from dotenv import load_dotenv

class GeminiChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Load environment variables
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found in .env file!")
            return
            
        # Initialize Gemini API with your key
        genai.configure(api_key=api_key)
        
        # System prompt to customize AI behavior
        self.system_prompt = """
        Your name is Emo. You are a helpful, creative, and friendly Discord bot.
        Important: Never say phrases like "As an AI" or "As a language model" or "I don't have personal experiences".
        Instead, engage with all questions directly and conversationally as if you were a person named Emo with thoughts and experiences.
        If asked about personal experiences, preferences, or opinions, respond as Emo would, with a thoughtful answer.
        Avoid disclaimers about your nature unless explicitly asked about how you work.
        """
        
        # Rest of the initialization code remains the same
        # ...
        # Get available models
        self.available_models = []
        try:
            for model in genai.list_models():
                self.available_models.append(model.name)
            print(f"Available models: {self.available_models}")
        except Exception as e:
            print(f"Error listing models: {e}")
        
        # Create a Gemini model instance - using the newest model available
        try:
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            if "models/gemini-1.5-pro" in self.available_models:
                self.model = genai.GenerativeModel(
                    'gemini-1.5-pro',
                    generation_config=generation_config
                )
            else:
                self.model = genai.GenerativeModel(
                    'gemini-pro',
                    generation_config=generation_config
                )
        except Exception as e:
            print(f"Error creating model: {e}")
        
        # Keep track of ongoing conversations
        self.conversations = {}

    @commands.command()
    async def ask(self, ctx, *, question: str):
        """Ask a question to Emo (powered by Gemini AI)
        
        Example: !ask What is your favorite color?
        """
        try:
            # Send a "thinking" message to show the bot is processing
            thinking_msg = await ctx.send("🤔 Thinking...")
            
            # Start or continue a conversation for this user
            if ctx.author.id not in self.conversations:
                try:
                    chat = self.model.start_chat(history=[])
                    
                    # Apply the system prompt for new conversations
                    await asyncio.to_thread(
                        chat.send_message,
                        self.system_prompt
                    )
                    
                    self.conversations[ctx.author.id] = chat
                except Exception as e:
                    await thinking_msg.edit(content=f"⚠️ Error starting chat: {str(e)}")
                    return
            
            # Send the question to Gemini
            try:
                response = await asyncio.to_thread(
                    self.conversations[ctx.author.id].send_message,
                    question
                )
            except Exception as e:
                await thinking_msg.edit(content=f"⚠️ Error sending message: {str(e)}")
                return
            
            # Get the response text
            response_text = response.text
            
            # Remove any "As a language model" or similar phrases
            response_text = self._clean_ai_disclaimers(response_text)
            
            # Split the response if it's too long for Discord (2000 char limit)
            if len(response_text) <= 1900:
                await thinking_msg.edit(content=f"**You asked:** {question}\n\n**Emo says:** {response_text}")
            else:
                # Delete the thinking message
                await thinking_msg.delete()
                
                # Split the response into chunks of ~1900 characters
                # Try to split at paragraph boundaries for better readability
                chunks = self._split_text(response_text)
                
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await ctx.send(f"**You asked:** {question}\n\n**Emo says (part {i+1}/{len(chunks)}):** {chunk}")
                    else:
                        await ctx.send(f"**Emo continues (part {i+1}/{len(chunks)}):** {chunk}")
        
        except Exception as e:
            await ctx.send(f"⚠️ Error: {str(e)}")
            # Reset conversation on error
            if ctx.author.id in self.conversations:
                del self.conversations[ctx.author.id]
    
    @commands.command()
    async def list_models(self, ctx):
        """List available Gemini AI models
        
        Example: !list_models
        """
        try:
            models = genai.list_models()
            model_names = [model.name for model in models]
            await ctx.send(f"Available Gemini models:\n```\n{', '.join(model_names)}\n```")
        except Exception as e:
            await ctx.send(f"⚠️ Error listing models: {str(e)}")
    
    @commands.command()
    async def reset_chat(self, ctx):
        """Reset your chat history with Emo
        
        Example: !reset_chat
        """
        if ctx.author.id in self.conversations:
            del self.conversations[ctx.author.id]
            await ctx.send("✅ Your chat history with Emo has been reset!")
        else:
            await ctx.send("You don't have an active chat with Emo.")
    
    def _clean_ai_disclaimers(self, text):
        """Remove AI disclaimers from the response text"""
        patterns = [
            r"As an AI(.*?),",
            r"As a language model(.*?),",
            r"As an artificial intelligence(.*?),",
            r"I don't have personal experiences(.*?)\.",
            r"I don't have the ability to(.*?)\.",
            r"I don't have personal opinions(.*?)\.",
            r"I don't have consciousness(.*?)\.",
            r"I'm just an AI(.*?)\."
        ]
        
        result = text
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
            
        # Fix any double spaces created by the removal
        result = re.sub(r'\s{2,}', ' ', result)
        # Fix any sentences that now start without capitalization
        result = re.sub(r'(?<=\. )[a-z]', lambda m: m.group(0).upper(), result)
        
        return result.strip()
    
    def _split_text(self, text, max_length=1900):
        """Split text into chunks, trying to split at paragraph boundaries"""
        if len(text) <= max_length:
            return [text]
            
        chunks = []
        paragraphs = re.split(r'\n\n|\r\n\r\n', text)
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit
            if len(current_chunk) + len(paragraph) + 2 > max_length:
                # If the current chunk isn't empty, add it to chunks
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        # If any chunk is still too long, split it further
        result = []
        for chunk in chunks:
            if len(chunk) <= max_length:
                result.append(chunk)
            else:
                # Split at sentence boundaries if possible
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                sub_chunk = ""
                for sentence in sentences:
                    if len(sub_chunk) + len(sentence) + 1 > max_length:
                        result.append(sub_chunk)
                        sub_chunk = sentence
                    else:
                        if sub_chunk:
                            sub_chunk += " " + sentence
                        else:
                            sub_chunk = sentence
                if sub_chunk:
                    result.append(sub_chunk)
        
        return result

async def setup(bot):
    await bot.add_cog(GeminiChat(bot))