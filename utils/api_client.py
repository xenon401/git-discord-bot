# utils/api_client.py

import aiohttp

class APIClient:
    BASE_URL = "https://api.jikan.moe/v4"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def search_manga(self, query):
        params = {"q": query, "limit": 25}
        async with self.session.get(f"{self.BASE_URL}/manga", params=params) as resp:
            data = await resp.json()
            return data.get("data", [])

    async def get_manga_characters(self, mal_id):
        async with self.session.get(f"{self.BASE_URL}/manga/{mal_id}/characters") as resp:
            data = await resp.json()
            return data.get("data", [])

    async def get_character_details(self, mal_id):
        async with self.session.get(f"{self.BASE_URL}/characters/{mal_id}") as resp:
            data = await resp.json()
            return data.get("data", None)

    async def get(self, url, params=None):
        async with self.session.get(url, params=params) as resp:
            return await resp.json()
