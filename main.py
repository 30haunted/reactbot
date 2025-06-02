import re
import asyncio
import discord
from dotenv import load_dotenv
import os
from PIL import Image
import io
import platform

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables")

client = discord.Client(self_bot=True)

active_reactions = {}

@client.event
async def on_ready():
    clear_cmd = 'cls' if platform.system() == 'Windows' else 'clear'
    os.system(clear_cmd)

    user = client.user
    print(f"Logged in as user: {user.display_name}")

@client.event
async def on_message(message):
    if message.author != client.user:
        return

    content = message.content.strip()

    # === Reaction Control ===
    if re.match(r'^stop\s+react$', content, re.IGNORECASE) or content.lower() == "sr":
        active_reactions.clear()
        try:
            await message.add_reaction("✅")
        except Exception:
            await message.channel.send("`Stopped reacting to all users.`")
        return

    if re.match(r'^stop\s+react\s+<@!?(\d+)>$', content, re.IGNORECASE) or re.match(r'^stop\s+react\s+\d+$', content, re.IGNORECASE):
        match = re.search(r'<@!?(\d+)>', content)
        user_id = int(match.group(1)) if match else int(content.split()[2])
        active_reactions.pop(user_id, None)
        await message.channel.send("`Stopped reacting to them.`")
        return

    if re.match(r'^react\s+<@!?(\d+)>', content, re.IGNORECASE) or re.match(r'^react\s+\d+', content, re.IGNORECASE):
        match = re.search(r'<@!?(\d+)>', content)
        user_id = int(match.group(1)) if match else int(content.split()[1])
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await message.channel.send("`Please provide emoji(s) to react with.`")
            return
        emojis = parts[2].split()
        active_reactions[user_id] = emojis
        await message.channel.send("`Started reacting.`")
        return

    # === WHOIS Command ===
    if re.match(r'^wi\s+<@!?(\d+)>$', content, re.IGNORECASE) or re.match(r'^wi\s+\d+$', content, re.IGNORECASE):
        match = re.search(r'<@!?(\d+)>', content)
        user_id = int(match.group(1)) if match else int(content.split()[1])

        try:
            user = await client.fetch_user(user_id)
        except Exception:
            await message.channel.send("`Could not fetch user.`")
            return

        embed = discord.Embed(title=f"Whois: {user}", color=0x3498db)
        embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)

        if message.guild:
            member = message.guild.get_member(user_id)
            if not member:
                try:
                    member = await message.guild.fetch_member(user_id)
                except Exception:
                    member = None

            if member:
                basic_perms = {
                    "read_messages", "send_messages", "view_channel", "read_message_history",
                    "connect", "speak", "use_voice_activation", "send_tts_messages",
                    "embed_links", "attach_files", "add_reactions", "use_external_emojis",
                    "view_guild_insights", "change_nickname", "send_messages_in_threads",
                    "create_public_threads", "create_private_threads", "use_external_stickers",
                }

                perms = member.guild_permissions
                elevated = [name.replace("_", " ").title() for name, value in perms if value and name not in basic_perms]
                value = ", ".join(elevated) if elevated else "None"
                embed.add_field(name="Elevated Permissions", value=value, inline=False)
            else:
                embed.add_field(name="Elevated Permissions", value="N/A (Not in guild)", inline=False)

        await message.channel.send(embed=embed)
        return

    # === Delete Last 2 Self Messages ===
    if content.lower() == "dw":
        def is_me(m):
            return m.author.id == client.user.id

        try:
            msgs = [m async for m in message.channel.history(limit=50)]
            my_msgs = [m for m in msgs if is_me(m)]
            to_delete = my_msgs[:2]
            if not to_delete:
                await message.channel.send("`No messages found to delete.`")
                return
            for msg in to_delete:
                try:
                    await msg.delete()
                    await asyncio.sleep(0.25)
                except Exception:
                    pass
        except Exception as e:
            await message.channel.send(f"`Failed to delete messages: {e}`")
        return

    # === Global Avatar ===
    if re.match(r'^av\s+<@!?(\d+)>$', content, re.IGNORECASE) or re.match(r'^av\s+\d+$', content, re.IGNORECASE):
        match = re.search(r'<@!?(\d+)>', content)
        user_id = int(match.group(1)) if match else int(content.split()[1])
        try:
            user = await client.fetch_user(user_id)
        except Exception:
            await message.channel.send("`Could not fetch user.`")
            return

        if user.avatar:
            fmt = "gif" if user.avatar.is_animated() else "png"
            url = user.avatar.replace(format=fmt, size=512).url
            await message.channel.send(f"{user}'s global avatar:\n{url}")
        else:
            await message.channel.send(f"{user} has no avatar.")
        return

    # === Server Avatar ===
    if re.match(r'^sav\s+<@!?(\d+)>$', content, re.IGNORECASE) or re.match(r'^sav\s+\d+$', content, re.IGNORECASE):
        if not message.guild:
            await message.channel.send("`This command must be used in a server.`")
            return
        match = re.search(r'<@!?(\d+)>', content)
        user_id = int(match.group(1)) if match else int(content.split()[1])
        member = message.guild.get_member(user_id)
        if not member:
            try:
                member = await message.guild.fetch_member(user_id)
            except Exception:
                member = None
        if not member:
            await message.channel.send("`Member not found in this server.`")
            return

        avatar = member.guild_avatar or member.avatar
        if avatar:
            fmt = "gif" if avatar.is_animated() else "png"
            url = avatar.replace(format=fmt, size=512).url
            await message.channel.send(f"{member}'s server avatar:\n{url}")
        else:
            await message.channel.send(f"{member} has no avatar.")
        return

    # === Convert Last Image to GIF ===
    if content.lower() == "gif":
        async for msg in message.channel.history(limit=20):
            if msg.author == client.user:
                for attachment in msg.attachments:
                    if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                        try:
                            img_bytes = await attachment.read()
                            img = Image.open(io.BytesIO(img_bytes))
                            gif_bytes = io.BytesIO()
                            img.save(gif_bytes, format="GIF", save_all=True, loop=0)
                            gif_bytes.seek(0)
                            file = discord.File(fp=gif_bytes, filename="converted.gif")
                            await message.channel.send(file=file)
                            return
                        except Exception as e:
                            await message.channel.send(f"`Failed to convert image: {e}`")
                            return
        await message.channel.send("`No recent image found to convert.`")
        return

    # === Auto React ===
    author_id = message.author.id
    if author_id in active_reactions:
        for emoji_str in active_reactions[author_id]:
            try:
                emoji = discord.PartialEmoji.from_str(emoji_str) if emoji_str.startswith('<') else emoji_str
                await message.add_reaction(emoji)
                await asyncio.sleep(0.75)
            except Exception:
                continue

client.run(TOKEN)
