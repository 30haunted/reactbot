import discord
import re
import asyncio
import sys
import os
import io
import aiohttp
from PIL import Image
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
TOKEN = os.getenv("TOKEN")

client = discord.Client(self_bot=True)

active_reactions = {}
last_wi_message = None
last_si_message = None

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global last_wi_message, last_si_message

    if message.author != client.user:
        author_id = message.author.id
        if author_id in active_reactions:
            for emoji_str in active_reactions[author_id]:
                try:
                    emoji = discord.PartialEmoji.from_str(emoji_str) if emoji_str.startswith('<') else emoji_str
                    await message.add_reaction(emoji)
                    await asyncio.sleep(0.75)
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        print("[Rate Limited] Waiting before retrying reaction.")
                    continue
        return

    content = message.content.strip().lower()

    if content == "quit":
        await message.channel.send("`Are you sure you want to quit? (y/n)`")

        def check(m):
            return m.author == client.user and m.channel == message.channel and m.content.lower() in ['y', 'yes', 'n', 'no']

        try:
            reply = await client.wait_for("message", check=check, timeout=15)
            if reply.content.lower() in ['y', 'yes']:
                await message.channel.send("`Shutting down in 3 seconds...`")
                await asyncio.sleep(3)
                await client.close()
                sys.exit(0)
            else:
                await message.channel.send("`Shutdown cancelled.`")
        except asyncio.TimeoutError:
            await message.channel.send("`No response. Shutdown cancelled.`")
        return

    if content == "sr":
        await asyncio.sleep(1.5)
        try:
            await message.clear_reactions()
        except Exception:
            pass
        await message.add_reaction("✅")
        active_reactions.clear()
        return

    match = re.match(r'^stop\s+react\s+<@!?(\d+)>$', content)
    if match:
        user_id = int(match.group(1))
        active_reactions.pop(user_id, None)
        await message.channel.send("`Stopped reacting to them.`")
        return

    match = re.match(r'^react\s+<@!?(\d+)>', content)
    if match:
        user_id = int(match.group(1))
        emoji_part = message.content.split(maxsplit=2)[-1]
        emojis = re.findall(r'<a?:[a-zA-Z0-9_]+:\d+>|[\U0001F000-\U0010FFFF]', emoji_part)

        if not emojis:
            await message.channel.send("`No valid emojis found.`")
            return

        if user_id not in active_reactions:
            active_reactions[user_id] = set()
        active_reactions[user_id].update(emojis)

        await message.channel.send("`Started reacting.`")
        return

    if content == "sh":
        await message.channel.send("~dispense")
        return

    match = re.match(r'^wi\s+(<@!?(\d+)>|(\d+))$', message.content, re.IGNORECASE)
    if match:
        user_id = int(match.group(2) or match.group(3))
        member = message.guild.get_member(user_id) if message.guild else None

        try:
            user = member or await client.fetch_user(user_id)
            user_info = f"```ini\n"
            user_info += f"[Username] {user.name}#{user.discriminator}\n"
            user_info += f"[User ID] {user.id}\n"
            user_info += f"[Created At] {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if member:
                user_info += f"[Nickname] {member.nick or 'None'}\n"
                user_info += f"[Joined Server] {member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

                perms = [perm[0].replace('_', ' ').title() for perm in member.guild_permissions if perm[1]]
                user_info += f"[Permissions] {', '.join(perms) if perms else 'None'}\n"

            user_info += "```"
            last_wi_message = await message.channel.send(user_info)
        except Exception:
            await message.channel.send("`Could not fetch user info.`")
        return

    if content == "si" and message.guild:
        guild = message.guild
        owner = guild.owner or await guild.fetch_member(guild.owner_id)

        info = f"```ini\n"
        info += f"[Server Name] {guild.name}\n"
        info += f"[Server ID] {guild.id}\n"
        info += f"[Owner] {owner}\n"
        info += f"[Created At] {guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        info += f"[Members] {guild.member_count}\n"
        info += f"[Channels] {len(guild.channels)}\n"
        info += f"[Roles] {len(guild.roles)}\n"
        info += f"```"

        last_si_message = await message.channel.send(info)
        return

    if content == "dw":
        deleted_any = False
        try:
            if last_wi_message:
                await last_wi_message.delete()
                last_wi_message = None
                deleted_any = True
        except Exception as e:
            await message.channel.send(f"`Failed to delete wi message: {e}`")

        try:
            if last_si_message:
                await last_si_message.delete()
                last_si_message = None
                deleted_any = True
        except Exception as e:
            await message.channel.send(f"`Failed to delete si message: {e}`")

        if deleted_any:
            await message.add_reaction("✅")
        else:
            await message.channel.send("`No wi or si message to delete.`")
        return

    if content == "gif":
        image_url = None

        if message.reference and isinstance(message.reference.resolved, discord.Message):
            replied_message = message.reference.resolved
            for att in replied_message.attachments:
                if att.filename.lower().endswith(("jpg", "jpeg", "png")):
                    image_url = att.url
                    break

        if not image_url:
            async for msg in message.channel.history(limit=10):
                for att in msg.attachments:
                    if att.filename.lower().endswith(("jpg", "jpeg", "png")):
                        image_url = att.url
                        break
                if image_url:
                    break

        if not image_url:
            await message.channel.send("`No image found to convert.`")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        await message.channel.send("`Failed to download image.`")
                        return
                    img_bytes = await resp.read()

            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            gif_buffer = io.BytesIO()
            image.save(gif_buffer, format="GIF")
            gif_buffer.seek(0)

            await message.channel.send(file=discord.File(fp=gif_buffer, filename="converted.gif"))

        except Exception as e:
            await message.channel.send(f"`GIF conversion failed: {e}`")
        return

    if content == "tt":
        tiktok_url = None

        async for msg in message.channel.history(limit=10):
            urls = re.findall(r'(https?://(?:www\.)?tiktok\.com/\S+)', msg.content)
            if urls:
                tiktok_url = urls[0]
                break

        if not tiktok_url:
            await message.channel.send("`No TikTok URL found in the message.`")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(tiktok_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            video_tag = soup.find("meta", property="og:video")
            video_url = video_tag["content"] if video_tag else None

            if not video_url:
                await message.channel.send("`No MP4 URL found on TikTok page.`")
                return

            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as resp:
                    if resp.status != 200:
                        await message.channel.send("`Failed to fetch TikTok video.`")
                        return
                    video_bytes = await resp.read()

            await message.channel.send(file=discord.File(io.BytesIO(video_bytes), filename="tiktok.mp4"))

        except Exception as e:
            await message.channel.send(f"`Error while processing TikTok: {e}`")
        return

client.run(TOKEN)
