import aiohttp
import random

async def fetch_meme(anime=True, sfw=True, nsfw=False):
    sources = []
    if anime:
        sources += ["AnimeMemes", "animememes", "goodanimemes"]
    if sfw:
        sources += ["memes", "dankmemes"]
    if nsfw:
        sources += ["NSFWmemes"]

    subreddit = random.choice(sources)
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
    headers = {"User-Agent": "DiscordMemeBot/1.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status != 200:
                return None
            posts = (await r.json())["data"]["children"]
            random.shuffle(posts)
            for post in posts:
                data = post["data"]
                if data.get("stickied") or (data.get("over_18", False) and not nsfw):
                    continue
                img = data.get("url_overridden_by_dest") or data.get("url")
                if img and (img.endswith(".jpg") or img.endswith(".png") or img.endswith(".jpeg") or img.endswith(".gif")):
                    return img
    return None
