from discord.ext import commands, tasks
import aiosqlite
import discord
import time
from utils import fetch_meme

class AutoMeme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meme_poster.start()

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def autopostmeme(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Auto Meme Poster Commands",
                description="Subcommands: enable, disable, channel, interval, anime, sfw, nsfw",
                color=discord.Color.blurple()
            )
            await ctx.send(embed=embed)

    @autopostmeme.command()
    async def enable(self, ctx):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO autopost_memes (guild_id, channel_id) VALUES (?, ?)",
                (str(ctx.guild.id), str(ctx.channel.id))
            )
            await db.execute(
                "UPDATE autopost_memes SET enabled = 1, channel_id = ? WHERE guild_id = ?",
                (str(ctx.channel.id), str(ctx.guild.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="Auto Meme Posting Enabled",
            description=f"Memes will be posted in {ctx.channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @autopostmeme.command()
    async def disable(self, ctx):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "UPDATE autopost_memes SET enabled = 0 WHERE guild_id = ?",
                (str(ctx.guild.id),)
            )
            await db.commit()
        embed = discord.Embed(
            title="Auto Meme Posting Disabled",
            description="No more memes will be automatically posted.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @autopostmeme.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "UPDATE autopost_memes SET channel_id = ? WHERE guild_id = ?",
                (str(channel.id), str(ctx.guild.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="Channel Set",
            description=f"Memes will be posted in {channel.mention}.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @autopostmeme.command()
    async def interval(self, ctx, minutes: int):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "UPDATE autopost_memes SET interval = ? WHERE guild_id = ?",
                (minutes, str(ctx.guild.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="Interval Set",
            description=f"Memes will be posted every {minutes} minutes.",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @autopostmeme.command()
    async def anime(self, ctx, value: bool):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "UPDATE autopost_memes SET anime = ? WHERE guild_id = ?",
                (int(value), str(ctx.guild.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="Anime Meme Setting Changed",
            description=f"Anime memes {'enabled' if value else 'disabled'}.",
            color=discord.Color.green() if value else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @autopostmeme.command()
    async def sfw(self, ctx, value: bool):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "UPDATE autopost_memes SET sfw = ? WHERE guild_id = ?",
                (int(value), str(ctx.guild.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="SFW Meme Setting Changed",
            description=f"SFW memes {'enabled' if value else 'disabled'}.",
            color=discord.Color.green() if value else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @autopostmeme.command()
    async def nsfw(self, ctx, value: bool):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "UPDATE autopost_memes SET nsfw = ? WHERE guild_id = ?",
                (int(value), str(ctx.guild.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="NSFW Meme Setting Changed",
            description=f"NSFW memes {'enabled' if value else 'disabled'}.",
            color=discord.Color.green() if value else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @tasks.loop(seconds=60)
    async def meme_poster(self):
        now = int(time.time())
        async with aiosqlite.connect(self.bot.db_path) as db:
            async with db.execute(
                "SELECT guild_id, channel_id, interval, anime, sfw, nsfw, last_post FROM autopost_memes WHERE enabled = 1"
            ) as cursor:
                for row in await cursor.fetchall():
                    guild_id, channel_id, interval, anime, sfw, nsfw, last_post = row
                    if now - (last_post or 0) < (interval or 60) * 60:
                        continue
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                    channel = guild.get_channel(int(channel_id))
                    if not channel:
                        continue
                    meme_url = await fetch_meme(anime=anime, sfw=sfw, nsfw=nsfw)
                    if meme_url:
                        embed = discord.Embed(
                            title="Random Meme",
                            color=discord.Color.random()
                        )
                        embed.set_image(url=meme_url)
                        await channel.send(embed=embed)
                        await db.execute(
                            "UPDATE autopost_memes SET last_post = ? WHERE guild_id = ?", (now, guild_id)
                        )
                        await db.commit()

def setup(bot):
    bot.add_cog(AutoMeme(bot))
