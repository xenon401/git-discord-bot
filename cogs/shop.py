from discord.ext import commands
import aiosqlite
import discord

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        async with aiosqlite.connect(self.bot.db_path) as db:
            async with db.execute("SELECT item_name, price, description FROM shop WHERE guild_id = ?", (str(ctx.guild.id),)) as cursor:
                items = await cursor.fetchall()
                if not items:
                    embed = discord.Embed(title="Shop", description="No items in the shop.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return
                embed = discord.Embed(title="🛒 Shop Items", color=discord.Color.purple())
                for item in items:
                    embed.add_field(
                        name=f"{item[0]} — {item[1]} coins",
                        value=item[2],
                        inline=False
                    )
                await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, *, item_name):
        async with aiosqlite.connect(self.bot.db_path) as db:
            async with db.execute(
                "SELECT price FROM shop WHERE guild_id = ? AND item_name = ?",
                (str(ctx.guild.id), item_name)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    embed = discord.Embed(title="Not Found", description="Item not found.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return
                price = row[0]
            async with db.execute(
                "SELECT balance FROM currency WHERE user_id = ? AND guild_id = ?",
                (str(ctx.author.id), str(ctx.guild.id))
            ) as cursor:
                row = await cursor.fetchone()
                balance = row[0] if row else 0
            if balance < price:
                embed = discord.Embed(title="Insufficient Funds", description="Not enough coins.", color=discord.Color.red())
                await ctx.send(embed=embed)
                return
            await db.execute(
                "UPDATE currency SET balance = balance - ? WHERE user_id = ? AND guild_id = ?",
                (price, str(ctx.author.id), str(ctx.guild.id))
            )
            await db.commit()
            embed = discord.Embed(title="Purchase Successful", description=f"You bought **{item_name}**!", color=discord.Color.green())
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Shop(bot))
