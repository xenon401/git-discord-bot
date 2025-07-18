from discord.ext import commands
import aiosqlite
import discord

CUSTOM_WORDS = ["hello", "thanks", "cool"]

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if any(word in message.content.lower() for word in CUSTOM_WORDS):
            async with aiosqlite.connect(self.bot.db_path) as db:
                await db.execute("""
                    INSERT INTO currency (user_id, guild_id, balance)
                    VALUES (?, ?, 1)
                    ON CONFLICT(user_id, guild_id)
                    DO UPDATE SET balance = balance + 1
                """, (str(message.author.id), str(message.guild.id)))
                await db.commit()

    @commands.command()
    async def bal(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiosqlite.connect(self.bot.db_path) as db:
            async with db.execute("SELECT balance FROM currency WHERE user_id = ? AND guild_id = ?",
                                  (str(member.id), str(ctx.guild.id))) as cursor:
                row = await cursor.fetchone()
                balance = row[0] if row else 0
        embed = discord.Embed(
            title="💰 Balance",
            description=f"{member.mention} has **{balance}** coins.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Currency(bot))
