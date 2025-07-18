from discord.ext import commands
import random
import discord

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, sides: int = 6):
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"{ctx.author.mention} rolled a **{result}** (1-{sides})",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))
