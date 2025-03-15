import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import re
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks  

class GeminiChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Load environment variables
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        mongo_uri = os.getenv('MONGO_URI')
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found in .env file!")
            return
            
        if not mongo_uri:
            print("WARNING: MONGO_URI not found in .env file!")
            print("Falling back to in-memory storage. Conversations will be lost on restart.")
            self.use_mongo = False
            self.conversations = {}
        else:
            # Initialize MongoDB connection
            try:
                self.mongo_client = MongoClient(mongo_uri)
                self.db = self.mongo_client['emo_bot']
                self.conversations_collection = self.db['conversations']
                self.messages_collection = self.db['conversation_messages']
                self.use_mongo = True
                print("Successfully connected to MongoDB")
                
                # Create indexes for faster queries
                self.conversations_collection.create_index("conversation_key")
                self.messages_collection.create_index("conversation_id")
                self.messages_collection.create_index("timestamp")
                
                # Setup periodic cleanup of old conversations (runs once per day)
                self.cleanup_old_conversations.start()
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                print("Falling back to in-memory storage. Conversations will be lost on restart.")
                self.use_mongo = False
                self.conversations = {}
            
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
            
            # Try to use the best available model with fallbacks
            if "models/gemini-2.0-flash" in self.available_models:
                self.model = genai.GenerativeModel(
                    'gemini-2.0-flash',
                    generation_config=generation_config
                )
            elif "models/gemini-1.5-flash" in self.available_models:
                self.model = genai.GenerativeModel(
                    'gemini-1.5-flash',
                    generation_config=generation_config
                )
            elif "models/gemini-1.5-pro" in self.available_models:
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

    @tasks.loop(hours=24)
    async def cleanup_old_conversations(self):
        """Clean up conversations older than 30 days"""
        if not self.use_mongo:
            return
            
        try:
            # Find conversations with no activity in the last 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            old_conversations = self.conversations_collection.find(
                {"last_updated": {"$lt": thirty_days_ago}}
            )
            
            # Delete the conversations and their messages
            for conv in old_conversations:
                self.messages_collection.delete_many({"conversation_id": conv["_id"]})
                self.conversations_collection.delete_one({"_id": conv["_id"]})
                
            print(f"Cleaned up old conversations")
        except Exception as e:
            print(f"Error during conversation cleanup: {e}")

    async def get_conversation(self, conversation_key):
        """Get or create a conversation"""
        if not self.use_mongo:
            # In-memory fallback
            if conversation_key not in self.conversations:
                chat = self.model.start_chat(history=[])
                # Apply the system prompt for new conversations
                await asyncio.to_thread(chat.send_message, self.system_prompt)
                self.conversations[conversation_key] = chat
            return self.conversations[conversation_key]
        else:
            # MongoDB implementation
            conversation = self.conversations_collection.find_one({"conversation_key": conversation_key})
            
            if not conversation:
                # Create a new conversation in the database
                conversation_id = self.conversations_collection.insert_one({
                    "conversation_key": conversation_key,
                    "created_at": datetime.now(timezone.utc),
                    "last_updated": datetime.now(timezone.utc)
                }).inserted_id
                
                # Start a new chat with Gemini
                chat = self.model.start_chat(history=[])
                # Apply system prompt and store it
                response = await asyncio.to_thread(chat.send_message, self.system_prompt)
                
                # Store system prompt in messages collection
                self.messages_collection.insert_one({
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": self.system_prompt,
                    "is_system_prompt": True,
                    "timestamp": datetime.now(timezone.utc)
                })
                
                self.messages_collection.insert_one({
                    "conversation_id": conversation_id,
                    "role": "model",
                    "content": response.text,
                    "is_system_prompt": True,
                    "timestamp": datetime.now(timezone.utc)
                })
                
                return chat
            else:
                # Restore conversation from database
                chat = self.model.start_chat(history=[])
                messages = self.messages_collection.find(
                    {"conversation_id": conversation["_id"]}
                ).sort("timestamp", 1)  # Sort by timestamp ascending
                
                # Restore message history to the chat
                for msg in messages:
                    if msg.get("is_system_prompt", False):
                        continue  # Skip the system prompt, it's already been applied
                    
                    # Simulate the message exchange to rebuild history
                    if msg["role"] == "user":
                        try:
                            response = await asyncio.to_thread(chat.send_message, msg["content"])
                            # Verify the response matches what we have stored
                            stored_response = self.messages_collection.find_one({
                                "conversation_id": conversation["_id"],
                                "role": "model",
                                "timestamp": {"$gt": msg["timestamp"]}
                            }, sort=[("timestamp", 1)])
                            
                            if stored_response and response.text != stored_response["content"]:
                                print("Warning: Restored response doesn't match stored response")
                        except Exception as e:
                            print(f"Error restoring conversation: {e}")
                            # If we encounter an error, start a fresh chat
                            return self.model.start_chat(history=[])
                
                # Update last accessed timestamp
                self.conversations_collection.update_one(
                    {"_id": conversation["_id"]},
                    {"$set": {"last_updated": datetime.now(timezone.utc)}}
                )
                
                return chat

    async def store_message(self, conversation_key, user_message, ai_response):
        """Store message history in MongoDB"""
        if not self.use_mongo:
            return  # No need to store if not using MongoDB
            
        try:
            # Find the conversation document
            conversation = self.conversations_collection.find_one({"conversation_key": conversation_key})
            if not conversation:
                return
                
            # Store user message
            self.messages_collection.insert_one({
                "conversation_id": conversation["_id"],
                "role": "user",
                "content": user_message,
                "is_system_prompt": False,
                "timestamp": datetime.now(timezone.utc)
            })
            
            # Store AI response
            self.messages_collection.insert_one({
                "conversation_id": conversation["_id"],
                "role": "model",
                "content": ai_response,
                "is_system_prompt": False,
                "timestamp": datetime.now(timezone.utc)
            })
            
            # Update last_updated timestamp
            self.conversations_collection.update_one(
                {"_id": conversation["_id"]},
                {"$set": {"last_updated": datetime.now(timezone.utc)}}
            )
        except Exception as e:
            print(f"Error storing messages: {e}")

    @commands.command()
    async def ask(self, ctx, *, question: str):
        """Ask a question to Emo (powered by Gemini AI)
        
        Example: !ask What is your favorite color?
        """
        try:
            # Send a "thinking" message to show the bot is processing
            thinking_msg = await ctx.send("🤔 Thinking...")
            
            # Create a composite key with channel ID and user ID for channel-specific memory
            conversation_key = f"{ctx.channel.id}_{ctx.author.id}"
            
            # Get or create conversation
            try:
                chat = await self.get_conversation(conversation_key)
            except Exception as e:
                await thinking_msg.edit(content=f"⚠️ Error starting chat: {str(e)}")
                return
            
            # Send the question to Gemini
            try:
                response = await asyncio.to_thread(
                    chat.send_message,
                    question
                )
            except Exception as e:
                await thinking_msg.edit(content=f"⚠️ Error sending message: {str(e)}")
                return
            
            # Get the response text
            response_text = response.text
            
            # Remove any "As a language model" or similar phrases
            response_text = self._clean_ai_disclaimers(response_text)
            
            # Store the message pair in MongoDB if available
            await self.store_message(conversation_key, question, response_text)
            
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
            if not self.use_mongo:
                conversation_key = f"{ctx.channel.id}_{ctx.author.id}"
                if conversation_key in self.conversations:
                    del self.conversations[conversation_key]
    
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
        """Reset your chat history with Emo in this channel
        
        Example: !reset_chat
        """
        conversation_key = f"{ctx.channel.id}_{ctx.author.id}"
        
        if not self.use_mongo:
            if conversation_key in self.conversations:
                del self.conversations[conversation_key]
                await ctx.send("✅ Your chat history with Emo has been reset for this channel!")
            else:
                await ctx.send("You don't have an active chat with Emo in this channel.")
        else:
            # MongoDB implementation
            conversation = self.conversations_collection.find_one({"conversation_key": conversation_key})
            if conversation:
                # Delete all messages for this conversation
                self.messages_collection.delete_many({"conversation_id": conversation["_id"]})
                # Delete the conversation itself
                self.conversations_collection.delete_one({"_id": conversation["_id"]})
                await ctx.send("✅ Your chat history with Emo has been reset for this channel!")
            else:
                await ctx.send("You don't have an active chat with Emo in this channel.")
    
    @commands.command()
    async def reset_all_chats(self, ctx):
        """Reset all your chat histories with Emo across all channels
        
        Example: !reset_all_chats
        """
        user_id = ctx.author.id
        
        if not self.use_mongo:
            # Find all conversations for this user
            user_conversations = [key for key in self.conversations.keys() if key.endswith(f"_{user_id}")]
            
            if user_conversations:
                # Delete all conversations for this user
                for key in user_conversations:
                    del self.conversations[key]
                await ctx.send(f"✅ All your chat histories with Emo have been reset across {len(user_conversations)} channels!")
            else:
                await ctx.send("You don't have any active chats with Emo.")
        else:
            # MongoDB implementation
            pattern = f".*_{user_id}$"
            cursor = self.conversations_collection.find({"conversation_key": {"$regex": pattern}})
            
            conversation_count = 0
            conversation_ids = []
            
            # Collect all conversation IDs first
            for conversation in cursor:
                conversation_ids.append(conversation["_id"])
                conversation_count += 1
                
            # Then delete all messages and conversations
            if conversation_ids:
                for conv_id in conversation_ids:
                    # Delete all messages for this conversation
                    self.messages_collection.delete_many({"conversation_id": conv_id})
                    # Delete the conversation itself
                    self.conversations_collection.delete_one({"_id": conv_id})
                
                await ctx.send(f"✅ All your chat histories with Emo have been reset across {conversation_count} channels!")
            else:
                await ctx.send("You don't have any active chats with Emo.")
    
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
    
    def cog_unload(self):
        """Clean up resources when the cog is unloaded"""
        if self.use_mongo:
            self.cleanup_old_conversations.cancel()
            self.mongo_client.close()

async def setup(bot):
    await bot.add_cog(GeminiChat(bot))