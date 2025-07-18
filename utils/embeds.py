# utils/embeds.py

import discord

class EmbedBuilder:
    @staticmethod
    def create_embed(title: str, description: str, color: int = 0x5865F2) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=color)

    @staticmethod
    def error_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=discord.Color.red())

    @staticmethod
    def info_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=discord.Color.blurple())

    @staticmethod
    def manga_embed(title: str, manga: dict) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=manga.get("synopsis", "No synopsis available."),
            color=discord.Color.purple()
        )
        embed.add_field(name="Title", value=manga.get("title", "N/A"), inline=True)
        if manga.get("title_english"):
            embed.add_field(name="English Title", value=manga["title_english"], inline=True)
        if manga.get("score"):
            embed.add_field(name="Score", value=str(manga["score"]), inline=True)
        if manga.get("status"):
            embed.add_field(name="Status", value=manga["status"], inline=True)
        if manga.get("episodes"):
            embed.add_field(name="Episodes", value=str(manga["episodes"]), inline=True)
        if manga.get("image"):
            embed.set_thumbnail(url=manga["image"])
        return embed

    @staticmethod
    def character_embed(character: dict) -> discord.Embed:
        embed = discord.Embed(
            title=character.get("name", "Character"),
            description=character.get("about", "No bio available."),
            color=discord.Color.teal()
        )
        if character.get("image"):
            embed.set_thumbnail(url=character["image"])
        if character.get("nicknames"):
            embed.add_field(name="Nicknames", value=", ".join(character["nicknames"]), inline=False)
        if character.get("favorites"):
            embed.add_field(name="Favorites", value=str(character["favorites"]), inline=True)
        return embed
