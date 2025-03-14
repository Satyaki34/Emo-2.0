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
            name="!mkgrp [@person1] [@person2] ...",
            value="Creates a private text room for you and mentioned friends.\n"
                 "Example: `!mkgrp @JohnDoe @JaneDoe`",
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
            name="!ask [question]",
            value="Ask Emo a question or have a conversation.\n"
                 "Example: `!ask What's your favorite movie?`",
            inline=False
        )
        
        embed.add_field(
            name="!reset_chat",
            value="Reset your conversation history with Emo.\n"
                 "Example: `!reset_chat`",
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
    async def mkgrp(self, ctx, *members: discord.Member):
        """Creates a private text channel for the command invoker and mentioned members."""
        # Check if any members were mentioned
        if not members:
            await ctx.send("Please mention at least one member to create a group with.")
            return
            
        # Check if the user mentioned themselves
        if ctx.author in members:
            await ctx.send("You don't need to mention yourself, you're automatically included.")
            
        # Filter out the author and bots
        valid_members = [member for member in members if member != ctx.author and not member.bot]
        
        # Check if there are any valid members left
        if not valid_members:
            await ctx.send("No valid members to create a group with. Please mention real users who aren't bots.")
            return

        guild = ctx.guild
        category_name = "Private Groups"
        
        # Find or create the "Private Groups" category
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)
            await category.set_permissions(guild.default_role, read_messages=False)
        
        # Create a name for the channel using the first few members' names
        member_names = [member.display_name for member in valid_members[:3]]
        if len(valid_members) > 3:
            member_names.append(f"+{len(valid_members)-3}")
            
        channel_name = f"private-{ctx.author.display_name}-{'-'.join(member_names)}"
        # Ensure the channel name isn't too long for Discord
        if len(channel_name) > 100:
            channel_name = channel_name[:97] + "..."
        
        # Create the channel
        channel = await guild.create_text_channel(
            channel_name, 
            category=category, 
            topic=f"Creator: {ctx.author.id}"
        )
        
        # Set permissions for the default role
        await channel.set_permissions(guild.default_role, read_messages=False)
        
        # Set permissions for the creator
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        
        # Set permissions for the bot
        await channel.set_permissions(self.bot.user, read_messages=True, send_messages=True)

        # Set permissions for each member
        mention_list = [ctx.author.mention]
        for member in valid_members:
            await channel.set_permissions(member, read_messages=True, send_messages=True)
            mention_list.append(member.mention)
        
        # Send welcome message
        members_str = ", ".join(mention_list)
        await channel.send(f"Welcome to your private group! Members: {members_str}")
        
        # Confirmation message
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
        
        # Delete voice channel if it exists
        if ", Voice: " in ctx.channel.topic:
            voice_channel_id = int(ctx.channel.topic.split(", Voice: ")[1])
            voice_channel = ctx.guild.get_channel(voice_channel_id)
            if voice_channel:
                await voice_channel.delete()
        
        await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(PrivateGroups(bot))