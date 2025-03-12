import discord
from discord.ext import commands

class PrivateGroups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def list(self, ctx):
        """Lists all available commands with descriptions and usage information."""
        embed = discord.Embed(
            title="Bot Commands List",
            description="Here are all the available commands and how to use them:",
            color=discord.Color.blue()
        )
        
        # Add your custom robot image as the thumbnail
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1083281523383480380/1349256619162341406/42ef8567-f4f1-4dc3-83ee-ed19a5d9a013-600x600.webp?ex=67d270a5&is=67d11f25&hm=b6a562e73ea4b553164a62a8c31ace5825ec9c3888d29cb78eae36bb5d3ba06b&=&format=webp")
        
        # Add command descriptions with their syntax
        embed.add_field(
            name="!mkgrp [@person_name]",
            value="Creates a private text room for you and your friend.\n"
                 "Example: `!mkgrp @JohnDoe`",
            inline=False
        )
        
        embed.add_field(
            name="!mkvc",
            value="Creates a private voice channel linked to the current private text channel.\n"
                 "Can only be used by the creator in a private group text channel.\n"
                 "Example: `!mkvc`",
            inline=False
        )
        
        embed.add_field(
            name="!delvc",
            value="Deletes the voice channel linked to the current private text channel.\n"
                 "Can only be used by the creator in a private group text channel.\n"
                 "Example: `!delvc`",
            inline=False
        )
        
        embed.add_field(
            name="!delgrp",
            value="Deletes the private text channel and its linked voice channel.\n"
                 "Can only be used by the creator in a private group text channel.\n"
                 "Example: `!delgrp`",
            inline=False
        )
        
        embed.add_field(
            name="!test",
            value="Simple test command to check if the bot is working.\n"
                 "Example: `!test`",
            inline=False
        )
        
        embed.add_field(
            name="!list",
            value="Shows this list of commands.\n"
                 "Example: `!list`",
            inline=False
        )
        
        embed.set_footer(text="For more help, contact a server administrator.")
        
        await ctx.send(embed=embed)

    @commands.command()
    async def mkgrp(self, ctx, member: discord.Member):
        """Creates a private text channel for the command invoker and a mentioned member."""
        if member == ctx.author:
            await ctx.send("You cannot create a group with yourself.")
            return
        if member.bot:
            await ctx.send("You cannot create a group with a bot.")
            return

        guild = ctx.guild
        category_name = "Private Groups"
        
        # Find or create the "Private Groups" category
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)
            await category.set_permissions(guild.default_role, read_messages=False)
        
        channel_name = "private-group"
        channel = await guild.create_text_channel(
            channel_name, 
            category=category, 
            topic=f"Creator: {ctx.author.id}"
        )
        
        # Set permissions
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        await channel.set_permissions(member, read_messages=True, send_messages=True)
        await channel.set_permissions(self.bot.user, read_messages=True, send_messages=True)
        
        await channel.send(f"Welcome {ctx.author.mention} and {member.mention} to your private group!")
        await ctx.send(f"Private group created for {ctx.author.mention} and {member.mention}.")

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
        
        # Delete voice channel if it exists
        if ", Voice: " in ctx.channel.topic:
            voice_channel_id = int(ctx.channel.topic.split(", Voice: ")[1])
            voice_channel = ctx.guild.get_channel(voice_channel_id)
            if voice_channel:
                await voice_channel.delete()
        
        await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(PrivateGroups(bot))