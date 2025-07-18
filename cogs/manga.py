import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional

from utils.embeds import EmbedBuilder
from utils.api_client import APIClient
from config import Config

MAX_OPTIONS = 25  # Discord's select limit

# --- UI Components ---

class MangaSelect(discord.ui.Select):
    def __init__(self, manga_list: List[dict], page: int, total_pages: int):
        options = []
        for manga in manga_list:
            title = manga['title']
            if len(title) > 100:
                title = title[:97] + "..."
            options.append(
                discord.SelectOption(
                    label=title,
                    description=f"Score: {manga.get('score', 'N/A')}/10" if manga.get('score') else "No score",
                    value=str(manga['mal_id'])
                )
            )
        placeholder = f"Select a manga... (Page {page+1}/{total_pages})"
        super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)
        self.manga_list = manga_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_id = int(self.values[0])
        selected_manga = next((m for m in self.manga_list if m['mal_id'] == selected_id), None)
        if not selected_manga:
            return await interaction.followup.send(
                embed=EmbedBuilder.error_embed("Error", "Selected manga not found."),
                ephemeral=True
            )
        embed = EmbedBuilder.manga_embed("Manga Details", selected_manga)
        view = CharacterView(selected_manga['mal_id'])
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class MangaPaginationView(discord.ui.View):
    def __init__(self, manga_results: List[dict]):
        super().__init__(timeout=120)
        self.manga_results = manga_results
        self.page = 0
        self.total_pages = (len(manga_results) - 1) // MAX_OPTIONS + 1
        self.generate_select()

    def generate_select(self):
        self.clear_items()
        start = self.page * MAX_OPTIONS
        end = start + MAX_OPTIONS
        page_manga = self.manga_results[start:end]
        self.add_item(MangaSelect(page_manga, self.page, self.total_pages))
        if self.total_pages > 1:
            self.add_item(PageLeftButton(self))
            self.add_item(PageRightButton(self))

class PageLeftButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬅️ Prev", row=1)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.page > 0:
            self.view_ref.page -= 1
            self.view_ref.generate_select()
            embed = EmbedBuilder.info_embed(
                "📚 Manga Search Results",
                f"Page {self.view_ref.page+1}/{self.view_ref.total_pages}"
            )
            await interaction.response.edit_message(embed=embed, view=self.view_ref)

class PageRightButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.secondary, label="Next ➡️", row=1)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.page < self.view_ref.total_pages - 1:
            self.view_ref.page += 1
            self.view_ref.generate_select()
            embed = EmbedBuilder.info_embed(
                "📚 Manga Search Results",
                f"Page {self.view_ref.page+1}/{self.view_ref.total_pages}"
            )
            await interaction.response.edit_message(embed=embed, view=self.view_ref)

class CharacterSelect(discord.ui.Select):
    def __init__(self, characters: List[dict]):
        options = []
        for character in characters[:25]:
            name = character['name']
            if len(name) > 100:
                name = name[:97] + "..."
            options.append(
                discord.SelectOption(
                    label=name,
                    value=str(character['mal_id'])
                )
            )
        super().__init__(placeholder="Select a character...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_id = int(self.values[0])
        async with APIClient() as client:
            character_details = await client.get_character_details(selected_id)
        if not character_details:
            return await interaction.followup.send(
                embed=EmbedBuilder.error_embed("Error", "Failed to get character details."),
                ephemeral=True
            )
        embed = EmbedBuilder.character_embed(character_details)
        await interaction.followup.send(embed=embed, ephemeral=True)

class CharacterView(discord.ui.View):
    def __init__(self, manga_id: int):
        super().__init__(timeout=120)
        self.manga_id = manga_id

    @discord.ui.button(label="View Characters", style=discord.ButtonStyle.primary, emoji="👥")
    async def view_characters(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        async with APIClient() as client:
            characters = await client.get_manga_characters(self.manga_id)
        if not characters:
            return await interaction.followup.send(
                embed=EmbedBuilder.error_embed("No Characters", "No characters found for this manga."),
                ephemeral=True
            )
        view = discord.ui.View()
        view.add_item(CharacterSelect(characters))
        embed = EmbedBuilder.info_embed(
            "Character Selection",
            f"Found {len(characters)} characters. Select one to view details:"
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# --- The Cog ---

class Manga(commands.Cog):
    """Manga and anime search commands."""

    def __init__(self, bot):
        self.bot = bot

    # --- Helper: shared handler for prefix and slash command ---
    async def _search_manga(self, ctxorinteraction, query: str, ephemeral=False):
        if len(query) < 2:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("Invalid Query", "Search query must be at least 2 characters long."),
                ephemeral=ephemeral
            )
        async with APIClient() as client:
            manga_results = await client.search_manga(query)
        if not manga_results:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("No Results", f"No manga found for '{query}'."),
                ephemeral=ephemeral
            )
        embed = EmbedBuilder.info_embed(
            "📚 Manga Search Results",
            f"Found {len(manga_results)} manga for '{query}'. Select one to view details:"
        )
        view = MangaPaginationView(manga_results)
        await self._send_embed(ctxorinteraction, embed, view=view, ephemeral=ephemeral)

    # --- Prefix Command ---
    @commands.command(name="manga")
    async def manga_prefix(self, ctx, *, query: str):
        """Search for manga (prefix command)"""
        await ctx.typing()
        await self._search_manga(ctx, query, ephemeral=False)

    # --- No-Prefix support: handled externally in on_message ---

    # --- Slash Command ---
    @app_commands.command(name="manga", description="Search for manga")
    @app_commands.describe(query="Manga title to search for")
    async def manga_slash(self, interaction: discord.Interaction, query: str):
        """Search for manga (slash)"""
        await interaction.response.defer(thinking=True)
        await self._search_manga(interaction, query, ephemeral=True)

    # --- Anime search (prefix & slash) ---
    async def _search_anime(self, ctxorinteraction, query: str, ephemeral=False):
        if len(query) < 2:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("Invalid Query", "Search query must be at least 2 characters long."),
                ephemeral=ephemeral
            )
        async with APIClient() as client:
            params = {'q': query, 'limit': 20, 'type': 'anime'}
            data = await client.get("https://api.jikan.moe/v4/anime", params=params)
        if not data or 'data' not in data:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("No Results", f"No anime found for '{query}'."),
                ephemeral=ephemeral
            )
        anime_results = []
        for item in data['data']:
            anime_results.append({
                'mal_id': item.get('mal_id'),
                'title': item.get('title'),
                'title_english': item.get('title_english'),
                'synopsis': item.get('synopsis'),
                'score': item.get('score'),
                'status': item.get('status'),
                'episodes': item.get('episodes'),
                'image': item.get('images', {}).get('jpg', {}).get('image_url')
            })
        if not anime_results:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("No Results", f"No anime found for '{query}'."),
                ephemeral=ephemeral
            )
        embed = EmbedBuilder.info_embed(
            "📺 Anime Search Results",
            f"Found {len(anime_results)} anime for '{query}'. Select one to view details:"
        )
        view = MangaPaginationView(anime_results)
        await self._send_embed(ctxorinteraction, embed, view=view, ephemeral=ephemeral)

    @commands.command(name="anime")
    async def anime_prefix(self, ctx, *, query: str):
        """Search for anime (prefix command)"""
        await ctx.typing()
        await self._search_anime(ctx, query, ephemeral=False)

    @app_commands.command(name="anime", description="Search for anime")
    @app_commands.describe(query="Anime title to search for")
    async def anime_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)
        await self._search_anime(interaction, query, ephemeral=True)

    # --- Character search (prefix & slash) ---
    async def _search_character(self, ctxorinteraction, query: str, ephemeral=False):
        if len(query) < 2:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("Invalid Query", "Search query must be at least 2 characters long."),
                ephemeral=ephemeral
            )
        async with APIClient() as client:
            params = {'q': query, 'limit': 25}
            data = await client.get(Config.API_URLS['character_search'], params=params)
        if not data or 'data' not in data:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("No Results", f"No characters found for '{query}'."),
                ephemeral=ephemeral
            )
        characters = []
        for item in data['data']:
            characters.append({
                'mal_id': item.get('mal_id'),
                'name': item.get('name'),
                'image': item.get('images', {}).get('jpg', {}).get('image_url')
            })
        if not characters:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("No Results", f"No characters found for '{query}'."),
                ephemeral=ephemeral
            )
        embed = EmbedBuilder.info_embed(
            "👤 Character Search Results",
            f"Found {len(characters)} characters for '{query}'. Select one to view details:"
        )
        view = discord.ui.View()
        view.add_item(CharacterSelect(characters))
        await self._send_embed(ctxorinteraction, embed, view=view, ephemeral=ephemeral)

    @commands.command(name="character")
    async def character_prefix(self, ctx, *, query: str):
        """Search for character (prefix command)"""
        await ctx.typing()
        await self._search_character(ctx, query, ephemeral=False)

    @app_commands.command(name="character", description="Search for a character")
    @app_commands.describe(query="Character name to search for")
    async def character_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)
        await self._search_character(interaction, query, ephemeral=True)

    # --- Random manga/anime ---
    async def _random_manga(self, ctxorinteraction, ephemeral=False):
        async with APIClient() as client:
            data = await client.get("https://api.jikan.moe/v4/random/manga")
        if not data or 'data' not in data:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("API Error", "Failed to get random manga."),
                ephemeral=ephemeral
            )
        manga_data = data['data']
        manga = {
            'mal_id': manga_data.get('mal_id'),
            'title': manga_data.get('title'),
            'title_english': manga_data.get('title_english'),
            'synopsis': manga_data.get('synopsis'),
            'score': manga_data.get('score'),
            'status': manga_data.get('status'),
            'image': manga_data.get('images', {}).get('jpg', {}).get('image_url')
        }
        embed = EmbedBuilder.manga_embed("Random Manga", manga)
        view = CharacterView(manga['mal_id'])
        await self._send_embed(ctxorinteraction, embed, view=view, ephemeral=ephemeral)

    @commands.command(name="randommanga")
    async def randommanga_prefix(self, ctx):
        """Get a random manga (prefix command)"""
        await ctx.typing()
        await self._random_manga(ctx, ephemeral=False)

    @app_commands.command(name="random-manga", description="Get a random manga")
    async def randommanga_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await self._random_manga(interaction, ephemeral=True)

    async def _random_anime(self, ctxorinteraction, ephemeral=False):
        async with APIClient() as client:
            data = await client.get("https://api.jikan.moe/v4/random/anime")
        if not data or 'data' not in data:
            return await self._send_embed(ctxorinteraction,
                EmbedBuilder.error_embed("API Error", "Failed to get random anime."),
                ephemeral=ephemeral
            )
        anime_data = data['data']
        anime = {
            'mal_id': anime_data.get('mal_id'),
            'title': anime_data.get('title'),
            'title_english': anime_data.get('title_english'),
            'synopsis': anime_data.get('synopsis'),
            'score': anime_data.get('score'),
            'status': anime_data.get('status'),
            'episodes': anime_data.get('episodes'),
            'image': anime_data.get('images', {}).get('jpg', {}).get('image_url')
        }
        embed = EmbedBuilder.manga_embed("Random Anime", anime)
        if anime.get('episodes'):
            embed.add_field(name="Episodes", value=f"📺 {anime['episodes']}", inline=True)
        view = CharacterView(anime['mal_id'])
        await self._send_embed(ctxorinteraction, embed, view=view, ephemeral=ephemeral)

    @commands.command(name="randomanime")
    async def randomanime_prefix(self, ctx):
        """Get a random anime (prefix command)"""
        await ctx.typing()
        await self._random_anime(ctx, ephemeral=False)

    @app_commands.command(name="random-anime", description="Get a random anime")
    async def randomanime_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await self._random_anime(interaction, ephemeral=True)

    # --- Helper: unified send (for ctx or interaction) ---
    async def _send_embed(self, ctxorinteraction, embed, view=None, ephemeral=False):
        try:
            if isinstance(ctxorinteraction, discord.Interaction):
                await ctxorinteraction.followup.send(embed=embed, view=view, ephemeral=ephemeral)
            else:
                await ctxorinteraction.send(embed=embed, view=view)
        except Exception as e:
            # fallback
            if isinstance(ctxorinteraction, discord.Interaction):
                await ctxorinteraction.followup.send(content="An error occurred.", ephemeral=True)
            else:
                await ctxorinteraction.send("An error occurred.")

async def setup(bot):
    await bot.add_cog(Manga(bot))
