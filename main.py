import discord
from discord.ext import commands
import aiosqlite
import os
from config import TOKEN, DB_PATH, DEFAULT_PREFIX

intents = discord.Intents.all()

async def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT prefix FROM guilds WHERE guild_id = ?", (str(message.guild.id), )) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else DEFAULT_PREFIX

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.db_path = DB_PATH

async def db_setup():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id TEXT PRIMARY KEY,
                prefix TEXT DEFAULT '?'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS currency (
                user_id TEXT,
                guild_id TEXT,
                balance INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shop (
                guild_id TEXT,
                item_name TEXT,
                price INTEGER,
                description TEXT,
                PRIMARY KEY (guild_id, item_name)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS noprefix_roles (
                guild_id TEXT,
                role_id TEXT,
                PRIMARY KEY (guild_id, role_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS autopost_memes (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT,
                enabled INTEGER DEFAULT 0,
                interval INTEGER DEFAULT 60,
                anime INTEGER DEFAULT 1,
                sfw INTEGER DEFAULT 1,
                nsfw INTEGER DEFAULT 0,
                last_post INTEGER DEFAULT 0
            )
        """)
        await db.commit()

@bot.event
async def on_guild_join(guild):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO guilds (guild_id, prefix) VALUES (?, ?)", (str(guild.id), DEFAULT_PREFIX))
        await db.commit()

@bot.event
async def on_ready():
    await db_setup()
    print(f"Logged in as {bot.user}")

async def get_noprefix_roles(guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT role_id FROM noprefix_roles WHERE guild_id = ?", (str(guild_id),)) as cursor:
            return [row[0] for row in await cursor.fetchall()]

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    ctx = await bot.get_context(message)
    if not ctx.valid:
        roles = [str(role.id) for role in message.author.roles]
        allowed_roles = await get_noprefix_roles(message.guild.id)
        if set(roles) & set(allowed_roles):
            content = message.content
            for command in bot.commands:
                if content.lower().startswith(command.name.lower()):
                    message.content = f"{await get_prefix(bot, message)}{content}"
                    ctx = await bot.get_context(message)
                    await bot.invoke(ctx)
                    return
    await bot.process_commands(message)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN)
