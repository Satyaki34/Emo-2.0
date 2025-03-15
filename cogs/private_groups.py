# private_groups.py
import discord
from discord.ext import commands
from discord import SelectOption, ui

# Dropdown UI component - separated for potential reuse
class CommandsDropdown(ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            SelectOption(label="Private Group Commands", description="Commands for creating and managing private groups", value="private_groups"),
            SelectOption(label="Emo Chat Commands", description="Commands for chatting with Emo (AI assistant)", value="emo_chat"),
            SelectOption(label="D&D Game Commands", description="Commands for Dungeons & Dragons gameplay", value="dnd"),
            SelectOption(label="Character Creation Commands", description="Commands for creating and managing D&D characters", value="character"),
            SelectOption(label="Utility Commands", description="General utility commands", value="utility")
        ]
        super().__init__(placeholder="Select a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        if self.values[0] == "private_groups":
            embed = self.create_private_groups_embed()
        elif self.values[0] == "emo_chat":
            embed = self.create_emo_chat_embed()
        elif self.values[0] == "dnd":
            embed = self.create_dnd_embed()
        elif self.values[0] == "character":
            embed = self.create_character_embed()
        elif self.values[0] == "utility":
            embed = self.create_utility_embed()
        
        await interaction.response.edit_message(embed=embed, view=CommandsView(self.bot))

    def create_private_groups_embed(self):
        embed = discord.Embed(
            title="Private Group Commands",
            description="Commands for creating and managing private groups",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp")
        
        embed.add_field(
            name="!mkgrp [@person1] [@person2] ...",
            value="Creates a private text room for you and mentioned friends.\nExample: `!mkgrp @JohnDoe @JaneDoe`",
            inline=False
        )
        
        embed.add_field(
            name="!mkvc",
            value="Creates a private voice channel linked to the current private text channel.\nCan only be used by the creator.\nExample: `!mkvc`",
            inline=False
        )
        
        embed.add_field(
            name="!delvc",
            value="Deletes the voice channel linked to the current private text channel.\nCan only be used by the creator.\nExample: `!delvc`",
            inline=False
        )
        
        embed.add_field(
            name="!delgrp",
            value="Deletes the private text channel and its linked voice channel.\nCan only be used by the creator.\nExample: `!delgrp`",
            inline=False
        )
        
        embed.set_footer(text="Select another category from the dropdown menu")
        return embed
        
    def create_emo_chat_embed(self):
        embed = discord.Embed(
            title="Emo Chat Commands",
            description="Commands for chatting with Emo (AI assistant)",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp")
        embed.add_field(name="!ask [question]", value="Ask Emo a question.\nExample: `!ask What's your favorite movie?`", inline=False)
        embed.add_field(name="!reset_chat", value="Reset conversation history in this channel.\nExample: `!reset_chat`", inline=False)
        embed.add_field(name="!reset_all_chats", value="Reset all conversation histories.\nExample: `!reset_all_chats`", inline=False)
        embed.add_field(name="!list_models", value="List available AI models.\nExample: `!list_models`", inline=False)
        embed.set_footer(text="Select another category from the dropdown menu")
        return embed
        
    def create_dnd_embed(self):
        embed = discord.Embed(
            title="D&D Game Commands",
            description="Commands for Dungeons & Dragons gameplay",
            color=discord.Color.dark_green()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp")
        embed.add_field(name="!dnd", value="Setup a new D&D session.\nExample: `!dnd`", inline=False)
        embed.add_field(name="!dnd_status", value="Show current D&D status.\nExample: `!dnd_status`", inline=False)
        embed.add_field(name="!end_dnd", value="End current D&D game.\nExample: `!end_dnd`", inline=False)
        embed.set_footer(text="Select another category from the dropdown menu")
        return embed
        
    def create_character_embed(self):
        embed = discord.Embed(
            title="Character Creation Commands",
            description="Commands for creating and managing D&D characters",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp")
        embed.add_field(name="!creation", value="Create a new character for the current D&D game.\nExample: `!creation`", inline=False)
        embed.add_field(name="!view_character [@player]", value="View a character in the D&D game. If no player is specified, shows your character.\nExample: `!view_character @JohnDoe`", inline=False)
        embed.add_field(name="!list_characters", value="List all characters in the current D&D game.\nExample: `!list_characters`", inline=False)
        embed.set_footer(text="Select another category from the dropdown menu")
        return embed
        
    def create_utility_embed(self):
        embed = discord.Embed(
            title="Utility Commands",
            description="General utility commands",
            color=discord.Color.light_gray()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp")
        embed.add_field(name="!test", value="Test bot functionality.\nExample: `!test`", inline=False)
        embed.add_field(name="!list", value="Show this command list.\nExample: `!list`", inline=False)
        embed.set_footer(text="Select another category from the dropdown menu")
        return embed

class CommandsView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.add_item(CommandsDropdown(bot))

class PrivateGroups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def list(self, ctx):
        """Lists all available commands with descriptions and usage information."""
        embed = discord.Embed(
            title="Bot Commands List",
            description="Select a command category from the dropdown menu below.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp")
        embed.add_field(
            name="Available Categories",
            value="• Private Group Commands\n• Emo Chat Commands\n• D&D Game Commands\n• Character Creation Commands\n• Utility Commands",
            inline=False
        )
        embed.set_footer(text="Use the dropdown menu below to see specific commands")
        
        view = CommandsView(self.bot)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def mkgrp(self, ctx, *members: discord.Member):
        """Creates a private text channel for the command invoker and mentioned members."""
        if not members:
            await ctx.send("Please mention at least one member to create a group with.")
            return
            
        if ctx.author in members:
            await ctx.send("You don't need to mention yourself, you're automatically included.")
            
        valid_members = [member for member in members if member != ctx.author and not member.bot]
        
        if not valid_members:
            await ctx.send("No valid members to create a group with.")
            return

        guild = ctx.guild
        category_name = "Private Groups"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)
            await category.set_permissions(guild.default_role, read_messages=False)
        
        member_names = [member.display_name for member in valid_members[:3]]
        if len(valid_members) > 3:
            member_names.append(f"+{len(valid_members)-3}")
            
        channel_name = f"private-{ctx.author.display_name}-{'-'.join(member_names)}"
        if len(channel_name) > 100:
            channel_name = channel_name[:97] + "..."
        
        channel = await guild.create_text_channel(
            channel_name, 
            category=category, 
            topic=f"Creator: {ctx.author.id}"
        )
        
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        await channel.set_permissions(self.bot.user, read_messages=True, send_messages=True)

        mention_list = [ctx.author.mention]
        for member in valid_members:
            await channel.set_permissions(member, read_messages=True, send_messages=True)
            mention_list.append(member.mention)
        
        members_str = ", ".join(mention_list)
        await channel.send(f"Welcome to your private group! Members: {members_str}")
        await ctx.send(f"Private group created for {len(mention_list)} members.")

    @commands.command()
    async def mkvc(self, ctx):
        """Creates a private voice channel linked to the private text channel."""
        if ctx.channel.category is None or ctx.channel.category.name != "Private Groups":
            await ctx.send("This command can only be used in a private group text channel.")
            return
        if ctx.channel.topic is None or not ctx.channel.topic.startswith("Creator: "):
            await ctx.send("This is not a private group channel.")
            return
        
        creator_id = int(ctx.channel.topic.split(": ")[1].split(",")[0])
        if ctx.author.id != creator_id:
            await ctx.send("Only the creator can add a voice channel.")
            return
        
        if ", Voice: " in ctx.channel.topic:
            await ctx.send("A voice channel already exists for this group.")
            return
        
        guild = ctx.guild
        category = ctx.channel.category
        overwrites = ctx.channel.overwrites
        voice_channel = await guild.create_voice_channel(
            "private-voice", 
            category=category, 
            overwrites=overwrites
        )
        
        new_topic = f"{ctx.channel.topic}, Voice: {voice_channel.id}"
        await ctx.channel.edit(topic=new_topic)
        await ctx.send(f"Voice channel {voice_channel.name} has been created.")

    @commands.command()
    async def delvc(self, ctx):
        """Deletes the voice channel linked to the private text channel."""
        if ctx.channel.category is None or ctx.channel.category.name != "Private Groups":
            await ctx.send("This command can only be used in a private group text channel.")
            return
        if ctx.channel.topic is None or not ctx.channel.topic.startswith("Creator: "):
            await ctx.send("This is not a private group channel.")
            return
        
        creator_id = int(ctx.channel.topic.split(": ")[1].split(",")[0])
        if ctx.author.id != creator_id:
            await ctx.send("Only the creator can delete the voice channel.")
            return
        
        if ", Voice: " not in ctx.channel.topic:
            await ctx.send("There is no voice channel to delete.")
            return
        
        voice_channel_id = int(ctx.channel.topic.split(", Voice: ")[1])
        voice_channel = ctx.guild.get_channel(voice_channel_id)
        if voice_channel:
            await voice_channel.delete()
        
        new_topic = ctx.channel.topic.split(", Voice: ")[0]
        await ctx.channel.edit(topic=new_topic)
        await ctx.send("Voice channel has been deleted.")

    @commands.command()
    async def delgrp(self, ctx):
        """Deletes the private text channel and its linked voice channel."""
        if ctx.channel.category is None or ctx.channel.category.name != "Private Groups":
            await ctx.send("This command can only be used in a private group text channel.")
            return
        if ctx.channel.topic is None or not ctx.channel.topic.startswith("Creator: "):
            await ctx.send("This is not a private group channel.")
            return
    
        creator_id = int(ctx.channel.topic.split(": ")[1].split(",")[0])
        if ctx.author.id != creator_id:
            await ctx.send("Only the creator can delete the group.")
            return
    
        if ", Voice: " in ctx.channel.topic:
            voice_channel_id = int(ctx.channel.topic.split(", Voice: ")[1])
            voice_channel = ctx.guild.get_channel(voice_channel_id)
            if voice_channel:
                await voice_channel.delete()
    
        await ctx.send("This private group will be deleted in a few seconds...")
        await ctx.channel.delete()

# Setup function moved outside the class
async def setup(bot):
    await bot.add_cog(PrivateGroups(bot))