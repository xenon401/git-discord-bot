import discord
from discord.ext import commands
import aiohttp
import re

class WebhookTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def webhookembed(self, ctx, webhook_url: str, *, args):
        """
        Send an embed or webhook message.
        Usage: ?webhookembed <webhook_url> title=Title; description=Desc; color=0xRRGGBB; content=Text; image=url; footer=txt; author=name|url|icon; thumbnail=url
        """
        fields = {}
        for part in args.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                fields[k.strip().lower()] = v.strip()

        embed = discord.Embed()
        if "title" in fields:
            embed.title = fields["title"]
        if "description" in fields:
            embed.description = fields["description"]
        if "color" in fields:
            try:
                embed.color = discord.Color(int(fields["color"], 16))
            except Exception:
                pass
        if "image" in fields:
            embed.set_image(url=fields["image"])
        if "footer" in fields:
            embed.set_footer(text=fields["footer"])
        if "author" in fields:
            parts = fields["author"].split("|")
            name = parts[0]
            url = parts[1] if len(parts) > 1 else discord.Embed.Empty
            icon = parts[2] if len(parts) > 2 else discord.Embed.Empty
            embed.set_author(name=name, url=url, icon_url=icon)
        if "thumbnail" in fields:
            embed.set_thumbnail(url=fields["thumbnail"])
        content = fields.get("content", "")

        payload = {
            "content": content,
            "embeds": [embed.to_dict()]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as resp:
                if resp.status in [200, 204]:
                    await ctx.send("✅ Embed sent via webhook!")
                else:
                    await ctx.send(f"❌ Failed to send embed. HTTP status: {resp.status}")

    @commands.command()
    async def webhookedit(self, ctx, webhook_url: str, message_link: str, *, args):
        """
        Edit a webhook message by link.
        Usage: ?webhookedit <webhook_url> <message_link> title=...; description=...; content=... etc.
        (Can edit both content and embed. See webhookembed for all fields.)
        """
        # Extract message ID from message link
        match = re.match(r'https://discord.com/channels/\d+/\d+/(\d+)', message_link)
        if not match:
            await ctx.send("❌ Invalid message link.")
            return
        message_id = match.group(1)

        # Parse fields as above
        fields = {}
        for part in args.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                fields[k.strip().lower()] = v.strip()
        embed = discord.Embed()
        if "title" in fields:
            embed.title = fields["title"]
        if "description" in fields:
            embed.description = fields["description"]
        if "color" in fields:
            try:
                embed.color = discord.Color(int(fields["color"], 16))
            except Exception:
                pass
        if "image" in fields:
            embed.set_image(url=fields["image"])
        if "footer" in fields:
            embed.set_footer(text=fields["footer"])
        if "author" in fields:
            parts = fields["author"].split("|")
            name = parts[0]
            url = parts[1] if len(parts) > 1 else discord.Embed.Empty
            icon = parts[2] if len(parts) > 2 else discord.Embed.Empty
            embed.set_author(name=name, url=url, icon_url=icon)
        if "thumbnail" in fields:
            embed.set_thumbnail(url=fields["thumbnail"])
        content = fields.get("content", "")

        edit_url = webhook_url.rstrip("/") + f"/messages/{message_id}"
        payload = {
            "content": content,
            "embeds": [embed.to_dict()]
        }
        async with aiohttp.ClientSession() as session:
            async with session.patch(edit_url, json=payload) as resp:
                if resp.status in [200, 204]:
                    await ctx.send("✅ Webhook message edited!")
                else:
                    await ctx.send(f"❌ Failed to edit message. HTTP status: {resp.status}")

def setup(bot):
    bot.add_cog(WebhookTools(bot))
