from discord.ext import commands
import aiohttp
import discord

class Manga(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def manga(self, ctx, *, query):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://kitsu.io/api/edge/manga?filter[text]={query}") as resp:
                data = await resp.json()
                if not data["data"]:
                    await ctx.send(embed=discord.Embed(title="No Results", description="No manga found.", color=discord.Color.red()))
                    return
                manga = data["data"][0]["attributes"]
                embed = discord.Embed(
                    title=manga["canonicalTitle"],
                    description=manga.get("synopsis", "No synopsis available.")[:1000],
                    color=discord.Color.blue()
                )
                embed.add_field(name="Chapters", value=manga.get("chapterCount", "N/A"))
                embed.add_field(name="Status", value=manga.get("status", "N/A"))
                if manga.get("posterImage", {}).get("original"):
                    embed.set_thumbnail(url=manga["posterImage"]["original"])
                embed.set_footer(text="Powered by Kitsu.io")
                await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Manga(bot))
