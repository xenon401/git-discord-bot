import discord
from discord.ext import commands, tasks
import aiosqlite
import aiohttp
from bs4 import BeautifulSoup

class MangaUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_new_chapters.start()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmangaupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for manga updates."""
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO manga_updates_channel (guild_id, channel_id) VALUES (?, ?)",
                (str(ctx.guild.id), str(channel.id))
            )
            await db.commit()
        await ctx.send(
            embed=discord.Embed(
                title="Manga Updates Channel Set",
                description=f"Updates will be posted in {channel.mention}.",
                color=discord.Color.green()
            )
        )

    @tasks.loop(minutes=10)
    async def check_new_chapters(self):
        async with aiosqlite.connect(self.bot.db_path) as db:
            # Get all guilds and their channels for manga updates
            async with db.execute("SELECT guild_id, channel_id FROM manga_updates_channel") as cursor:
                guild_channels = await cursor.fetchall()

            # For demo: fetch the latest updates from mangakakatana
            url = "https://mangakakalot.com/manga_list?type=latest"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return
                    html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            updates = []
            # Find all latest manga updates
            for block in soup.select(".list-truyen-item-wrap"):
                title_tag = block.select_one("h3 a")
                chapter_tag = block.select_one(".chapter a")
                if not title_tag or not chapter_tag:
                    continue
                manga_title = title_tag.text.strip()
                manga_url = title_tag['href']
                chapter_name = chapter_tag.text.strip()
                chapter_url = chapter_tag['href']
                updates.append((manga_title, manga_url, chapter_name, chapter_url))

            for guild_id, channel_id in guild_channels:
                async with db.execute(
                    "SELECT chapter_url FROM manga_announced WHERE guild_id = ?", (guild_id,)
                ) as cursor:
                    announced = set(row[0] for row in await cursor.fetchall())
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    continue
                new_updates = [u for u in updates if u[3] not in announced]
                for manga_title, manga_url, chapter_name, chapter_url in new_updates:
                    embed = discord.Embed(
                        title=f"{manga_title} - {chapter_name}",
                        url=chapter_url,
                        description=f"New chapter released!",
                        color=discord.Color.blurple()
                    )
                    embed.add_field(name="Read Manga", value=f"[{manga_title}]({manga_url})")
                    await channel.send(embed=embed)
                    await db.execute(
                        "INSERT INTO manga_announced (guild_id, chapter_url) VALUES (?, ?)",
                        (guild_id, chapter_url)
                    )
                await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        # Ensure the tables exist
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS manga_updates_channel (guild_id TEXT PRIMARY KEY, channel_id TEXT)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS manga_announced (guild_id TEXT, chapter_url TEXT, PRIMARY KEY (guild_id, chapter_url))"
            )
            await db.commit()

def setup(bot):
    bot.add_cog(MangaUpdates(bot))
