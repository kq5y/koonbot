import enum
import datetime
import logging

import discord
from discord import app_commands

import config
import utils


class Categories(enum.Enum):
    web = "web"
    crypto = "crypto"
    rev = "rev"
    forensic = "forensic"
    pwn = "pwn"
    misc = "misc"
    blockchain = "blockchain"
    osint = "osint"
    ppc = "ppc"
    other = "other"


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = MyClient(intents=intents)
logger = logging.getLogger(__name__)


def is_ctf_channel(channel: discord.TextChannel) -> bool:
    return channel.name.startswith("🆙")


def is_ctf_thread(thread: discord.Thread) -> bool:
    parent = thread.parent
    if isinstance(parent, discord.TextChannel):
        return parent.name.startswith("🆙")
    return False


@client.tree.command(name="new-ctf", description="Create a new CTF channel")
async def new_ctf(
    interaction: discord.Interaction,
    ctf_name: str,
    category_name: discord.CategoryChannel = None
):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("😡Run it in the server.", ephemeral=True)
        return
    
    if not category_name:
        category_name = str(datetime.datetime.now().year)
    else:
        category_name = category_name.name
    
    sanitized_category = utils.sanitize_name(category_name)
    sanitized_ctf = utils.sanitize_name(ctf_name)
    display_category = category_name

    existing_category = discord.utils.get(guild.categories, name=sanitized_category)
    if existing_category is None:
        new_cat = await guild.create_category(sanitized_category)
        category_obj = new_cat
    else:
        category_obj = existing_category
    
    discord_channel_name = f"🆙{sanitized_ctf}"
    existing_channel = discord.utils.get(category_obj.text_channels, name=discord_channel_name)
    if existing_channel:
        await interaction.response.send_message(f"😡Channel `{ctf_name}` already exists in category `{display_category}`.", ephemeral=True)
        return
    
    await guild.create_text_channel(
        name=discord_channel_name,
        category=category_obj,
        reason="New CTF channel created by bot command"
    )
    await interaction.response.send_message(f"✅Created channel `{ctf_name}` in category `{display_category}`.", ephemeral=True)
    

@client.tree.command(name="new-chal", description="Create a new challenge thread in a CTF channel")
async def new_chal(
    interaction: discord.Interaction,
    category: Categories,
    challenge_name_1: str,
    challenge_name_2: str = None,
    challenge_name_3: str = None,
    challenge_name_4: str = None,
    challenge_name_5: str = None
):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("😡This command can only be used in a text channel.", ephemeral=True)
        return
    
    if not is_ctf_channel(channel):
        await interaction.response.send_message("😡This command can only be used in a CTF channel.", ephemeral=True)
        return
    
    name_list = [challenge_name_1, challenge_name_2, challenge_name_3, challenge_name_4, challenge_name_5]
    name_list = [name for name in name_list if name]
    if not name_list:
        await interaction.response.send_message("😡You must provide at least one challenge name.", ephemeral=True)
        return
    
    created_count = 0
    response_messages = []
    for name in name_list:
        thread_title = f"{category.value}: {name}"
        existing = discord.utils.get(channel.threads, name=thread_title)
        if existing:
            response_messages.append(f"😡Thread `{thread_title}` already exists.")
            continue

        await channel.create_thread(
            name=thread_title,
            type=discord.ChannelType.public_thread,
            reason="New challenge thread created by bot command",
        )
        created_count += 1
    
    if created_count == 0:
        response_messages.append("😡No new threads were created. All provided names already exist.")
    else:
        response_messages.append(f"✅Created {created_count} new challenge threads.")
    await interaction.response.send_message("\n".join(response_messages), ephemeral=True)
    

@client.tree.command(name="rename-chal", description="Rename a challenge thread")
async def rename_chal(
    interaction: discord.Interaction,
    new_name: str
):
    thread = interaction.channel
    if not isinstance(thread, discord.Thread):
        await interaction.response.send_message("😡This command can only be used in a thread.", ephemeral=True)
        return
    
    if not is_ctf_thread(thread):
        await interaction.response.send_message("😡This command can only be used in a CTF thread.", ephemeral=True)
        return
    
    sanitized_name = utils.sanitize_name(new_name)
    if not sanitized_name:
        await interaction.response.send_message("😡Invalid name provided.", ephemeral=True)
        return
    
    category_name = thread.name.split(":")[0].strip()
    new_thread_title = f"{category_name}: {sanitized_name}"

    existing_thread = discord.utils.get(thread.parent.threads, name=new_thread_title)
    if existing_thread and existing_thread.id != thread.id:
        await interaction.response.send_message(f"😡A thread with the name `{sanitized_name}` already exists.", ephemeral=True)
        return
    if thread.name == new_thread_title:
        await interaction.response.send_message("😡The thread is already named that.", ephemeral=True)
        return
    
    await thread.edit(name=existing_thread, reason="Challenge thread renamed by bot command")
    await interaction.response.send_message(f"✅Renamed thread to `{sanitized_name}`.", ephemeral=True)


@client.tree.command(name="solved", description="Mark a challenge as solved")
async def solved(
    interaction: discord.Interaction
):
    thread = interaction.channel
    if not isinstance(thread, discord.Thread):
        await interaction.response.send_message("😡This command can only be used in a thread.", ephemeral=True)
        return
    
    if not is_ctf_thread(thread):
        await interaction.response.send_message("😡This command can only be used in a CTF thread.", ephemeral=True)
        return
    
    current_name = thread.name
    if current_name.startswith("🚩"):
        await interaction.response.send_message("😡This challenge is already marked as solved.", ephemeral=True)
        return
    
    new_name = f"🚩 {current_name}"
    await thread.edit(name=new_name, reason="Challenge marked as solved by bot command")
    await interaction.response.send_message(f"✅Marked thread `{current_name}` as solved.", ephemeral=True)


@client.tree.command(name="unsolved", description="Unmark a challenge as solved")
async def unsolved(
    interaction: discord.Interaction
):
    thread = interaction.channel
    if not isinstance(thread, discord.Thread):
        await interaction.response.send_message("😡This command can only be used in a thread.", ephemeral=True)
        return
    
    if not is_ctf_thread(thread):
        await interaction.response.send_message("😡This command can only be used in a CTF thread.", ephemeral=True)
        return
    
    current_name = thread.name
    if not current_name.startswith("🚩"):
        await interaction.response.send_message("😡This challenge is not marked as solved.", ephemeral=True)
        return
    
    new_name = current_name.replace("🚩 ", "", 1)
    await thread.edit(name=new_name, reason="Challenge unmarked as solved by bot command")
    await interaction.response.send_message(f"✅Unmarked thread `{current_name}` as unsolved.", ephemeral=True)


@client.tree.command(name="end-ctf", description="End a CTF and archive its channel")
async def end_ctf(
    interaction: discord.Interaction
):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("😡This command can only be used in a text channel.", ephemeral=True)
        return
    
    if not is_ctf_channel(channel):
        await interaction.response.send_message("😡This command can only be used in a CTF channel.", ephemeral=True)
        return
    
    new_name = channel.name.replace("🆙", "", 1)
    await channel.edit(name=new_name, reason="CTF channel ended by bot command")
    await interaction.response.send_message(f"✅Ended CTF channel `{channel.name}`.", ephemeral=True)


@client.tree.command(name="unend-ctf", description="Unend a CTF and restore its channel")
async def unend_ctf(
    interaction: discord.Interaction
):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("😡This command can only be used in a text channel.", ephemeral=True)
        return
    
    if is_ctf_channel(channel):
        await interaction.response.send_message("😡This channel is already a CTF channel.", ephemeral=True)
        return
    
    new_name = f"🆙{channel.name}"
    await channel.edit(name=new_name, reason="CTF channel restored by bot command")
    await interaction.response.send_message(f"✅Restored CTF channel `{channel.name}`.", ephemeral=True)


@client.event
async def on_ready():
    logging.basicConfig(level=logging.INFO, force=True)
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    await client.change_presence(activity=discord.Game(name="koon"))
    
    guild = discord.Object(id=config.GUILD_ID) if config.GUILD_ID else None
    await client.tree.sync(guild=guild)
    logger.info("Command tree synced successfully.")


if __name__ == "__main__":
    client.run(config.DISCORD_TOKEN)
