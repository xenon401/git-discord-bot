from discord.ext import commands
import aiosqlite
import discord
from config import DB_PATH

class NoPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addnoprefixrole(self, ctx, role: discord.Role):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO noprefix_roles (guild_id, role_id) VALUES (?, ?)",
                (str(ctx.guild.id), str(role.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="No-Prefix Role Added",
            description=f"{role.mention} can now use bot commands without a prefix.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removenoprefixrole(self, ctx, role: discord.Role):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM noprefix_roles WHERE guild_id = ? AND role_id = ?",
                (str(ctx.guild.id), str(role.id))
            )
            await db.commit()
        embed = discord.Embed(
            title="No-Prefix Role Removed",
            description=f"{role.mention} can no longer use bot commands without a prefix.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(NoPrefix(bot))
