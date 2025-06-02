import re
import asyncio
import discord
from dotenv import load_dotenv
import os
from PIL import Image
import io
import platform
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables")

# No intents needed for discord.py-self
client = discord.Client(self_bot=True)

active_reactions = {}

async def safe_send(channel, content=None, **kwargs):
    """Helper function to safely send messages with error handling"""
    try:
        return await channel.send(content, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None

async def safe_react(message, emoji):
    """Helper function to safely add reactions with error handling"""
    try:
        await message.add_reaction(emoji)
        return True
    except discord.HTTPException as e:
        logger.error(f"Failed to react with {emoji}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error reacting: {e}")
        return False

@client.event
async def on_ready():
    clear_cmd = 'cls' if platform.system() == 'Windows' else 'clear'
    os.system(clear_cmd)

    user = client.user
    print(f"Logged in as user\nUsername: {user.name}#{user.discriminator}\nDisplay Name: {user.display_name}")

@client.event
async def on_message(message):
    if message.author != client.user:
        # Handle reactions to others' messages
        await handle_reactions(message)
        return

    content = message.content.strip()

    # === Reaction Control ===
    if re.match(r'^(stop\s+react|sr)(?:\s+<@!?(\d+)>|\s+(\d+))?$', content, re.IGNORECASE):
        await handle_stop_react(message, content)
        return

    if re.match(r'^react\s+(?:<@!?(\d+)>|(\d+))\s+(.+)$', content, re.IGNORECASE):
        await handle_react_command(message, content)
        return

    # === WHOIS Command ===
    if re.match(r'^wi\s+(?:<@!?(\d+)>|(\d+))$', content, re.IGNORECASE):
        await handle_whois(message, content)
        return

    # === Delete Last 2 Self Messages ===
    if content.lower() == "dw":
        await handle_delete_messages(message)
        return

    # === Global Avatar ===
    if re.match(r'^av\s+(?:<@!?(\d+)>|(\d+))$', content, re.IGNORECASE):
        await handle_global_avatar(message, content)
        return

    # === Server Avatar ===
    if re.match(r'^sav\s+(?:<@!?(\d+)>|(\d+))$', content, re.IGNORECASE):
        await handle_server_avatar(message, content)
        return

    # === Convert Last Image to GIF ===
    if content.lower() == "gif":
        await handle_gif_conversion(message)
        return

async def handle_reactions(message):
    """Handle auto-reactions to messages"""
    author_id = message.author.id
    if author_id not in active_reactions:
        return

    for emoji_str in active_reactions[author_id]:
        try:
            # Parse emoji
            if emoji_str.startswith('<'):
                # Handle custom emojis
                emoji = discord.PartialEmoji.from_str(emoji_str)
                if not emoji.id:  # Fallback for invalid custom emoji format
                    emoji = emoji_str
            else:
                # Handle unicode emojis
                emoji = emoji_str

            # Check if already reacted by you
            already_reacted = False
            for reaction in message.reactions:
                if str(reaction.emoji) == str(emoji):
                    async for user in reaction.users():
                        if user.id == client.user.id:
                            already_reacted = True
                            break
                    if already_reacted:
                        break

            if not already_reacted:
                success = await safe_react(message, emoji)
                if not success:
                    continue
                await asyncio.sleep(1.25)  # Rate limit protection
        except Exception as e:
            logger.error(f"Error in reaction handling: {e}")
            continue

async def handle_stop_react(message, content):
    """Handle stop react commands"""
    match = re.match(r'^(?:stop\s+react|sr)(?:\s+<@!?(\d+)>|\s+(\d+))?$', content, re.IGNORECASE)
    if not match:
        return

    if not match.group(1) and not match.group(2):
        # Stop all reactions
        active_reactions.clear()
        await safe_react(message, "✅")
        return
    
    # Stop reactions for specific user
    user_id = int(match.group(1) or match.group(2))
    active_reactions.pop(user_id, None)
    await safe_send(message.channel, "`Stopped reacting to them.`")

async def handle_react_command(message, content):
    """Handle react commands"""
    match = re.match(r'^react\s+(?:<@!?(\d+)>|(\d+))\s+(.+)$', content, re.IGNORECASE)
    if not match:
        return

    user_id = int(match.group(1) or match.group(2))
    emojis = match.group(3).split()
    
    # Validate emojis
    valid_emojis = []
    for emoji in emojis:
        if emoji.startswith('<:'):
            # Custom emoji format check
            if not re.match(r'^<a?:[a-zA-Z0-9_]{2,32}:\d+>$', emoji):
                continue
        valid_emojis.append(emoji)
    
    if not valid_emojis:
        await safe_send(message.channel, "`No valid emojis provided.`")
        return
    
    active_reactions[user_id] = valid_emojis
    await safe_send(message.channel, "`Started reacting.`")

async def handle_whois(message, content):
    """Handle whois command"""
    match = re.match(r'^wi\s+(?:<@!?(\d+)>|(\d+))$', content, re.IGNORECASE)
    if not match:
        return

    user_id = int(match.group(1) or match.group(2))

    try:
        user = await client.fetch_user(user_id)
    except discord.NotFound:
        await safe_send(message.channel, "`User not found.`")
        return
    except discord.HTTPException as e:
        await safe_send(message.channel, f"`Failed to fetch user: {e}`")
        return

    embed = discord.Embed(title=f"Whois: {user}", color=0x3498db)
    embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
    embed.add_field(name="User ID", value=user.id, inline=True)
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    
    # Handle avatar URL safely
    avatar_url = None
    if user.avatar:
        fmt = "gif" if user.avatar.is_animated() else "png"
        avatar_url = user.avatar.replace(format=fmt, size=256).url
        embed.set_thumbnail(url=avatar_url)

    if message.guild:
        member = message.guild.get_member(user_id)
        if not member:
            try:
                member = await message.guild.fetch_member(user_id)
            except (discord.NotFound, discord.HTTPException):
                member = None

        if member:
            # Add guild-specific information
            embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
            embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            
            # Handle roles
            if len(member.roles) > 1:  # Skip @everyone
                roles = ", ".join([r.name for r in reversed(member.roles[1:])])
                embed.add_field(name="Roles", value=roles[:1024] + ("..." if len(roles) > 1024 else ""), inline=False)

            # Check permissions
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
            embed.add_field(name="Guild Info", value="Not in this server", inline=False)

    await safe_send(message.channel, embed=embed)

async def handle_delete_messages(message):
    """Handle delete messages command"""
    def is_me(m):
        return m.author.id == client.user.id

    try:
        msgs = [m async for m in message.channel.history(limit=50)]
        my_msgs = [m for m in msgs if is_me(m)]
        to_delete = my_msgs[:2]
        
        if not to_delete:
            await safe_send(message.channel, "`No messages found to delete.`")
            return
        
        for msg in to_delete:
            try:
                await msg.delete()
                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                logger.error(f"Failed to delete message {msg.id}: {e}")
                continue
    except Exception as e:
        await safe_send(message.channel, f"`Failed to delete messages: {e}`")

async def handle_global_avatar(message, content):
    """Handle global avatar command"""
    match = re.match(r'^av\s+(?:<@!?(\d+)>|(\d+))$', content, re.IGNORECASE)
    if not match:
        return

    user_id = int(match.group(1) or match.group(2))
    
    try:
        user = await client.fetch_user(user_id)
    except discord.NotFound:
        await safe_send(message.channel, "`User not found.`")
        return
    except discord.HTTPException as e:
        await safe_send(message.channel, f"`Failed to fetch user: {e}`")
        return

    if not user.avatar:
        await safe_send(message.channel, f"{user} has no avatar.")
        return

    try:
        fmt = "gif" if user.avatar.is_animated() else "png"
        url = user.avatar.replace(format=fmt, size=1024).url
        await safe_send(message.channel, f"{user}'s global avatar:\n{url}")
    except Exception as e:
        await safe_send(message.channel, f"`Failed to get avatar URL: {e}`")

async def handle_server_avatar(message, content):
    """Handle server avatar command"""
    if not message.guild:
        await safe_send(message.channel, "`This command must be used in a server.`")
        return

    match = re.match(r'^sav\s+(?:<@!?(\d+)>|(\d+))$', content, re.IGNORECASE)
    if not match:
        return

    user_id = int(match.group(1) or match.group(2))
    
    try:
        member = await message.guild.fetch_member(user_id)
    except discord.NotFound:
        await safe_send(message.channel, "`Member not found in this server.`")
        return
    except discord.HTTPException as e:
        await safe_send(message.channel, f"`Failed to fetch member: {e}`")
        return

    avatar = member.guild_avatar or member.avatar
    if not avatar:
        await safe_send(message.channel, f"{member} has no avatar.")
        return

    try:
        fmt = "gif" if avatar.is_animated() else "png"
        url = avatar.replace(format=fmt, size=1024).url
        await safe_send(message.channel, f"{member}'s server avatar:\n{url}")
    except Exception as e:
        await safe_send(message.channel, f"`Failed to get avatar URL: {e}`")

async def handle_gif_conversion(message):
    """Handle GIF conversion command"""
    async for msg in message.channel.history(limit=20):
        if msg.author == client.user:
            for attachment in msg.attachments:
                if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    try:
                        img_bytes = await attachment.read()
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        # Create a palette for better GIF quality
                        if img.mode != 'P':
                            img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                        
                        gif_bytes = io.BytesIO()
                        img.save(gif_bytes, format="GIF", save_all=True, loop=0, optimize=True)
                        gif_bytes.seek(0)
                        
                        file = discord.File(fp=gif_bytes, filename="converted.gif")
                        await safe_send(message.channel, file=file)
                        return
                    except Exception as e:
                        await safe_send(message.channel, f"`Failed to convert image: {e}`")
                        return
    await safe_send(message.channel, "`No recent image found to convert.`")

client.run(TOKEN)
