import discord
import re
import asyncio

TOKEN = "YOUR_USER_TOKEN_HERE"

client = discord.Client(self_bot=True)

active_reactions = {}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Only respond to commands you send
    if message.author == client.user:
        content = message.content.strip()

        # Stop react command
        if re.match(r'^stop\s+react\s+<@!?(\d+)>$', content, re.IGNORECASE):
            user_id = int(re.search(r'<@!?(\d+)>', content).group(1))
            active_reactions.pop(user_id, None)
            await message.channel.send("`Stopped reacting to them.`")
            return

        # React command
        if re.match(r'^react\s+<@!?(\d+)>', content, re.IGNORECASE):
            user_id = int(re.search(r'<@!?(\d+)>', content).group(1))
            emoji_part = content.split(maxsplit=2)[-1]

            emojis = re.findall(r'<a?:[a-zA-Z0-9_]+:\d+>|[\U0001F000-\U0010FFFF]', emoji_part)

            if not emojis:
                await message.channel.send("`No valid emojis found.`")
                return

            if user_id not in active_reactions:
                active_reactions[user_id] = set()

            active_reactions[user_id].update(emojis)
            await message.channel.send("`Started reacting.`")
            return

    # React to messages by tracked users, in any channel (guild or DM)
    author_id = message.author.id
    if author_id in active_reactions:
        for emoji_str in active_reactions[author_id]:
            try:
                if emoji_str.startswith('<'):
                    emoji = discord.PartialEmoji.from_str(emoji_str)
                else:
                    emoji = emoji_str
                await message.add_reaction(emoji)
                await asyncio.sleep(0.75)  # delay to avoid rate limits
            except Exception:
                continue

client.run(TOKEN)
