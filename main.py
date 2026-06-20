import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask, request, jsonify
from threading import Thread
import asyncio
import datetime
import time
from pymongo import MongoClient
from functools import wraps

# MongoDB setup
mongo = None
db = None
warns_col = None
config_col = None

def init_mongo():
    global mongo, db, warns_col, config_col
    mongo = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    db = mongo["discordbot"]
    warns_col = db["warns"]
    config_col = db["config"]
    # Default config for main server
    if not config_col.find_one({"guild_id": "1471790587920388108"}):
        config_col.insert_one({
            "guild_id": "1471790587920388108",
            "logs_channel": "logs",
            "autorole": 1471790587920388114,
            "allowed_roles": [1471790588272836631, 1471790588272836630, 1511459295475142747],
            "safe_roles": [1471790588272836631, 1511459295475142747],
            "safe_password": "Digravina@21"
        })

def get_config(guild_id):
    doc = config_col.find_one({"guild_id": str(guild_id)})
    if not doc:
        doc = {
            "guild_id": str(guild_id),
            "logs_channel": "logs",
            "autorole": None,
            "allowed_roles": [],
            "safe_roles": [],
            "safe_password": "Digravina@21"
        }
        config_col.insert_one(doc)
    return doc

def update_config(guild_id, key, value):
    config_col.update_one({"guild_id": str(guild_id)}, {"$set": {key: value}}, upsert=True)

def get_warns(user_id):
    doc = warns_col.find_one({"user_id": str(user_id)})
    return doc["count"] if doc else 0

def set_warns(user_id, count):
    warns_col.update_one({"user_id": str(user_id)}, {"$set": {"count": count}}, upsert=True)

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.locked = False
bot.config_unlocked = {}  # {guild_id: unlock_timestamp}
bot.ready_event = None  # set in on_ready, used so Flask waits until bot is ready

OWNER_ID = 1251903591656980504
API_KEY = os.getenv("API_KEY")  # clé secrète pour protéger l'API, à définir sur Render

def is_config_unlocked(guild_id):
    unlock_time = bot.config_unlocked.get(guild_id)
    if unlock_time and time.time() - unlock_time < 900:  # 15 min
        return True
    return False

def has_allowed_role():
    async def predicate(interaction: discord.Interaction):
        if bot.locked and interaction.user.id != OWNER_ID:
            embed = discord.Embed(description="🔒 Bot is currently locked by the owner.", color=0xff0000)
            await interaction.response.send_message(embed=embed)
            return False
        cfg = get_config(interaction.guild_id)
        allowed = set(cfg.get("allowed_roles", []))
        user_roles = {role.id for role in interaction.user.roles}
        if not user_roles & allowed:
            embed = discord.Embed(description="❌ You don't have permission to use this command.", color=0xff0000)
            await interaction.response.send_message(embed=embed)
            return False
        return True
    return app_commands.check(predicate)

async def check_locked(interaction: discord.Interaction):
    if bot.locked and interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="🔒 Bot is currently locked by the owner.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return False
    return True

@bot.event
async def on_ready():
    init_mongo()
    try:
        await bot.tree.sync()
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")
    print(f"{bot.user} is online!")

# /ban
@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not await check_locked(interaction): return
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't ban this member, their role is too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(title="🔨 Member Banned", color=0xff0000)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.add_field(name="Banned by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(description="❌ I can't ban this member.", color=0xff0000)
        await interaction.response.send_message(embed=embed)

# /kick
@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not await check_locked(interaction): return
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't kick this member, their role is too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(title="👢 Member Kicked", color=0xff0000)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.add_field(name="Kicked by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(description="❌ I can't kick this member.", color=0xff0000)
        await interaction.response.send_message(embed=embed)

# /mute
@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int = 10, reason: str = "No reason provided"):
    if not await check_locked(interaction): return
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't mute this member, their role is too high.", color=0xff6600)
        await interaction.response.send_message(embed=embed)
        return
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="🔇 Member Muted", color=0xff6600)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.add_field(name="Muted by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
        embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(description="❌ I can't mute this member.", color=0xff6600)
        await interaction.response.send_message(embed=embed)

# /unmute
@bot.tree.command(name="unmute", description="Remove timeout from a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not await check_locked(interaction): return
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't unmute this member, their role is too high.", color=0xff6600)
        await interaction.response.send_message(embed=embed)
        return
    await member.timeout(None)
    embed = discord.Embed(title="🔊 Member Unmuted", color=0xff6600)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Unmuted by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# /unban
@bot.tree.command(name="unban", description="Unban a user by ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    if not await check_locked(interaction): return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        embed = discord.Embed(title="✅ Member Unbanned", color=0x00cc00)
        embed.add_field(name="User", value=f"**{user}**", inline=True)
        embed.add_field(name="Unbanned by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(description="❌ User not found or not banned.", color=0xff0000)
        await interaction.response.send_message(embed=embed)

# /warn
@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not await check_locked(interaction): return
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't warn this member, their role is too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    await interaction.response.defer()
    count = get_warns(member.id) + 1
    set_warns(member.id, count)
    embed = discord.Embed(title="⚠️ Member Warned", color=0xffcc00)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Warned by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Warnings", value=f"{count}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.followup.send(embed=embed)

# /unwarn
@bot.tree.command(name="unwarn", description="Remove a warning from a member")
@app_commands.checks.has_permissions(manage_messages=True)
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if not await check_locked(interaction): return
    await interaction.response.defer()
    count = get_warns(member.id)
    if count == 0:
        embed = discord.Embed(description=f"❌ **{member}** has no warnings.", color=0xff0000)
        await interaction.followup.send(embed=embed)
        return
    count -= 1
    set_warns(member.id, count)
    embed = discord.Embed(title="✅ Warning Removed", color=0xffcc00)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Unwarn by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    embed.add_field(name="Remaining Warnings", value=f"{count}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.followup.send(embed=embed)

# /warnings
@bot.tree.command(name="warnings", description="Check warnings of a member")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    if not await check_locked(interaction): return
    await interaction.response.defer()
    count = get_warns(member.id)
    embed = discord.Embed(title="📋 Warnings", color=0xffcc00)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Total Warnings", value=f"{count}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.followup.send(embed=embed)

# /clear
@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 10):
    if not await check_locked(interaction): return
    embed = discord.Embed(description=f"🗑️ Clearing **{amount}** messages...", color=0x3399ff)
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(2)
    await interaction.channel.purge(limit=amount + 1)

# /mutelist
@bot.tree.command(name="mutelist", description="List all muted members")
async def mutelist(interaction: discord.Interaction):
    if not await check_locked(interaction): return
    muted = [m for m in interaction.guild.members if m.is_timed_out()]
    if not muted:
        embed = discord.Embed(description="✅ No members are currently muted.", color=0x00cc00)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="🔇 Muted Members", color=0xff6600)
    for m in muted:
        until = m.timed_out_until.strftime("%Y-%m-%d %H:%M UTC")
        embed.add_field(name=f"{m}", value=f"Until: {until}", inline=False)
    await interaction.response.send_message(embed=embed)

# /roleadd
@bot.tree.command(name="roleadd", description="Give a role to a member")
@has_allowed_role()
async def roleadd(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't give this role, it's too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    if role in member.roles:
        embed = discord.Embed(description=f"❌ **{member}** already has the role {role.mention}.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    await member.add_roles(role)
    embed = discord.Embed(title="✅ Role Added", color=0x00cc00)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Added by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# /roleremove
@bot.tree.command(name="roleremove", description="Remove a role from a member")
@has_allowed_role()
async def roleremove(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't remove this role, it's too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    if role not in member.roles:
        embed = discord.Embed(description=f"❌ **{member}** doesn't have the role {role.mention}.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    await member.remove_roles(role)
    embed = discord.Embed(title="✅ Role Removed", color=0x00cc00)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Removed by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# /lock
@bot.tree.command(name="lock", description="Lock a channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not await check_locked(interaction): return
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Channel Locked", color=0xff0000)
    embed.add_field(name="Channel", value=channel.mention, inline=True)
    embed.add_field(name="Locked by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    await interaction.response.send_message(embed=embed)

# /unlock
@bot.tree.command(name="unlock", description="Unlock a channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not await check_locked(interaction): return
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Channel Unlocked", color=0x00cc00)
    embed.add_field(name="Channel", value=channel.mention, inline=True)
    embed.add_field(name="Unlocked by", value=f"**{interaction.user.top_role.name}** · {interaction.user.name}", inline=True)
    await interaction.response.send_message(embed=embed)

# /warnlist
@bot.tree.command(name="warnlist", description="List all warned members")
@app_commands.checks.has_permissions(manage_messages=True)
async def warnlist(interaction: discord.Interaction):
    if not await check_locked(interaction): return
    await interaction.response.defer()
    docs = warns_col.find({"count": {"$gt": 0}})
    warned = list(docs)
    if not warned:
        embed = discord.Embed(description="✅ No members have warnings.", color=0x00cc00)
        await interaction.followup.send(embed=embed)
        return
    embed = discord.Embed(title="⚠️ Warned Members", color=0xffcc00)
    for doc in warned:
        try:
            user = await bot.fetch_user(int(doc["user_id"]))
            embed.add_field(name=f"{user}", value=f"{doc['count']} warning(s)", inline=False)
        except:
            embed.add_field(name=f"Unknown ({doc['user_id']})", value=f"{doc['count']} warning(s)", inline=False)
    await interaction.followup.send(embed=embed)

# /banlist
@bot.tree.command(name="banlist", description="List all banned members")
@app_commands.checks.has_permissions(ban_members=True)
async def banlist(interaction: discord.Interaction):
    if not await check_locked(interaction): return
    await interaction.response.defer()
    bans = [entry async for entry in interaction.guild.bans()]
    if not bans:
        embed = discord.Embed(description="✅ No members are banned.", color=0x00cc00)
        await interaction.followup.send(embed=embed)
        return
    embed = discord.Embed(title="🔨 Banned Members", color=0xff0000)
    for entry in bans[:25]:
        embed.add_field(name=f"{entry.user}", value=f"Reason: {entry.reason or 'No reason'}", inline=False)
    await interaction.followup.send(embed=embed)

# /broadcast
@bot.tree.command(name="broadcast", description="Send a broadcast message")
@app_commands.checks.has_permissions(manage_messages=True)
async def broadcast(interaction: discord.Interaction, message: str, mention: str = "none"):
    if not await check_locked(interaction): return
    if mention == "everyone":
        ping = "@everyone"
    elif mention == "here":
        ping = "@here"
    else:
        role = discord.utils.get(interaction.guild.roles, name=mention)
        ping = role.mention if role else ""
    embed = discord.Embed(description=message, color=0x3399ff)
    embed.set_footer(text=f"📢 Sent by {interaction.user.top_role.name} · {interaction.user.name}")
    confirm = discord.Embed(description="✅ Broadcast sent!", color=0x00cc00)
    await interaction.response.send_message(embed=confirm, ephemeral=True)
    await interaction.channel.send(content=ping if ping else None, embed=embed)

# /safemode
class SafeModeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="✅ Give Roles", style=discord.ButtonStyle.green)
    async def give_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = get_config(interaction.guild_id)
        roles = [interaction.guild.get_role(r) for r in cfg.get("safe_roles", []) if interaction.guild.get_role(r)]
        if roles:
            await interaction.user.add_roles(*roles)
        embed = discord.Embed(title="✅ Roles Given", description=" ".join(r.mention for r in roles), color=0x00cc00)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔒 Lock Bot", style=discord.ButtonStyle.red)
    async def lock_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.locked = True
        embed = discord.Embed(title="🔒 Bot Locked", description="Bot is now locked for everyone except the owner.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔓 Unlock Bot", style=discord.ButtonStyle.green)
    async def unlock_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.locked = False
        embed = discord.Embed(title="🔓 Bot Unlocked", description="Bot is now unlocked for everyone.", color=0x00cc00)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="safemode", description="Owner only")
async def safemode(interaction: discord.Interaction, password: str):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    cfg = get_config(interaction.guild_id)
    if password != cfg.get("safe_password", "Digravina@21"):
        embed_public = discord.Embed(description=f"❌ **{interaction.user}** tried to use safemode with a wrong password.", color=0xff0000)
        await interaction.response.send_message(embed=embed_public)
        try:
            embed_dm = discord.Embed(title="⚠️ Safemode Alert", description=f"**{interaction.user}** (`{interaction.user.id}`) tried to use `/safemode` with a wrong password.", color=0xff0000)
            owner = await bot.fetch_user(OWNER_ID)
            await owner.send(embed=embed_dm)
        except:
            pass
        return
    embed = discord.Embed(title="🔐 Safe Mode", description="Choose an action:", color=0x3399ff)
    await interaction.response.send_message(embed=embed, view=SafeModeView(), ephemeral=True)

# /config
config_group = app_commands.Group(name="config", description="Configure the bot (owner only)")

@config_group.command(name="unlock", description="Unlock config for 15 minutes")
async def config_unlock(interaction: discord.Interaction, password: str):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    cfg = get_config(interaction.guild_id)
    if password != cfg.get("safe_password", "Digravina@21"):
        embed = discord.Embed(description="❌ Wrong password.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    bot.config_unlocked[interaction.guild_id] = time.time()
    embed = discord.Embed(title="🔓 Config Unlocked", description="Config is unlocked for 15 minutes.", color=0x00cc00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@config_group.command(name="logs", description="Set the logs channel")
async def config_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if not is_config_unlocked(interaction.guild_id):
        embed = discord.Embed(description="🔒 Use `/config unlock` first.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    update_config(interaction.guild_id, "logs_channel", channel.name)
    embed = discord.Embed(title="✅ Logs Channel Updated", description=f"Logs will now be sent to {channel.mention}", color=0x00cc00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@config_group.command(name="autorole", description="Set the auto-join role")
async def config_autorole(interaction: discord.Interaction, role: discord.Role):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if not is_config_unlocked(interaction.guild_id):
        embed = discord.Embed(description="🔒 Use `/config unlock` first.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    update_config(interaction.guild_id, "autorole", role.id)
    embed = discord.Embed(title="✅ Auto-Role Updated", description=f"New members will get {role.mention}", color=0x00cc00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@config_group.command(name="allowedroles", description="Set allowed roles for roleadd/roleremove (up to 3)")
async def config_allowedroles(interaction: discord.Interaction, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if not is_config_unlocked(interaction.guild_id):
        embed = discord.Embed(description="🔒 Use `/config unlock` first.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    roles = [r.id for r in [role1, role2, role3] if r]
    update_config(interaction.guild_id, "allowed_roles", roles)
    mentions = " ".join(r.mention for r in [role1, role2, role3] if r)
    embed = discord.Embed(title="✅ Allowed Roles Updated", description=mentions, color=0x00cc00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@config_group.command(name="saferoles", description="Set roles given by safemode (up to 3)")
async def config_saferoles(interaction: discord.Interaction, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if not is_config_unlocked(interaction.guild_id):
        embed = discord.Embed(description="🔒 Use `/config unlock` first.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    roles = [r.id for r in [role1, role2, role3] if r]
    update_config(interaction.guild_id, "safe_roles", roles)
    mentions = " ".join(r.mention for r in [role1, role2, role3] if r)
    embed = discord.Embed(title="✅ Safe Roles Updated", description=mentions, color=0x00cc00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@config_group.command(name="safepassword", description="Change the safemode password")
async def config_safepassword(interaction: discord.Interaction, new_password: str):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if not is_config_unlocked(interaction.guild_id):
        embed = discord.Embed(description="🔒 Use `/config unlock` first.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    update_config(interaction.guild_id, "safe_password", new_password)
    embed = discord.Embed(title="✅ Password Updated", description="Safemode password has been changed.", color=0x00cc00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@config_group.command(name="view", description="View current config")
async def config_view(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if not is_config_unlocked(interaction.guild_id):
        embed = discord.Embed(description="🔒 Use `/config unlock` first.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    cfg = get_config(interaction.guild_id)
    allowed = [f"<@&{r}>" for r in cfg.get("allowed_roles", [])]
    safe = [f"<@&{r}>" for r in cfg.get("safe_roles", [])]
    autorole = f"<@&{cfg['autorole']}>" if cfg.get("autorole") else "None"
    embed = discord.Embed(title="⚙️ Server Config", color=0x3399ff)
    embed.add_field(name="Logs Channel", value=f"#{cfg.get('logs_channel', 'logs')}", inline=True)
    embed.add_field(name="Auto-Role", value=autorole, inline=True)
    embed.add_field(name="Allowed Roles", value=" ".join(allowed) or "None", inline=False)
    embed.add_field(name="Safe Roles", value=" ".join(safe) or "None", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.tree.add_command(config_group)

# Logs
@bot.event
async def on_member_join(member):
    cfg = get_config(member.guild.id)
    autorole_id = cfg.get("autorole")
    if autorole_id:
        role = member.guild.get_role(autorole_id)
        if role:
            await member.add_roles(role)
    channel = discord.utils.get(member.guild.text_channels, name=cfg.get("logs_channel", "logs"))
    if channel:
        embed = discord.Embed(title="✅ Member Joined", color=0x00cc00)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    cfg = get_config(member.guild.id)
    channel = discord.utils.get(member.guild.text_channels, name=cfg.get("logs_channel", "logs"))
    if channel:
        embed = discord.Embed(title="❌ Member Left", color=0xff0000)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.guild is None or message.author.bot:
        return
    cfg = get_config(message.guild.id)
    channel = discord.utils.get(message.guild.text_channels, name=cfg.get("logs_channel", "logs"))
    if channel:
        embed = discord.Embed(title="🗑️ Message Deleted", color=0xff6600)
        embed.add_field(name="Author", value=f"**{message.author}**", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Content", value=message.content or "*(empty)*", inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.guild is None or before.author.bot:
        return
    cfg = get_config(before.guild.id)
    channel = discord.utils.get(before.guild.text_channels, name=cfg.get("logs_channel", "logs"))
    if channel:
        embed = discord.Embed(title="✏️ Message Edited", color=0x3399ff)
        embed.add_field(name="Author", value=f"**{before.author}**", inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content or "*(empty)*", inline=False)
        embed.add_field(name="After", value=after.content or "*(empty)*", inline=False)
        await channel.send(embed=embed)


# ============================================================
# ===================  API REST (App Android) =================
# ============================================================

api = Flask('')

def require_api_key(f):
    """Décorateur : vérifie le header X-API-Key sur chaque requête protégée."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not API_KEY:
            return jsonify({"error": "API_KEY not configured on server"}), 500
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

def run_coroutine(coro, timeout=10):
    """
    Exécute une coroutine discord.py depuis un thread Flask (sync),
    en la poussant dans l'event loop du bot, et attend le résultat.
    """
    future = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    return future.result(timeout=timeout)

@api.route('/')
def home():
    return "Bot is alive!"

@api.route('/api/health', methods=['GET'])
@require_api_key
def health():
    return jsonify({
        "online": bot.is_ready(),
        "locked": bot.locked,
        "guild_count": len(bot.guilds) if bot.is_ready() else 0
    })

@api.route('/api/guilds', methods=['GET'])
@require_api_key
def list_guilds():
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guilds = [{"id": str(g.id), "name": g.name, "member_count": g.member_count} for g in bot.guilds]
    return jsonify(guilds)

@api.route('/api/guilds/<guild_id>/stats', methods=['GET'])
@require_api_key
def guild_stats(guild_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    async def _stats():
        bans = [b async for b in guild.bans()]
        muted = [m for m in guild.members if m.is_timed_out()]
        return len(bans), len(muted)

    try:
        ban_count, muted_count = run_coroutine(_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    warned_count = warns_col.count_documents({"count": {"$gt": 0}})

    return jsonify({
        "guild_id": str(guild.id),
        "name": guild.name,
        "member_count": guild.member_count,
        "ban_count": ban_count,
        "muted_count": muted_count,
        "warned_count": warned_count,
        "locked": bot.locked
    })

@api.route('/api/guilds/<guild_id>/config', methods=['GET'])
@require_api_key
def get_guild_config(guild_id):
    cfg = get_config(guild_id)
    cfg.pop("_id", None)
    cfg.pop("safe_password", None)  # on ne renvoie jamais le mdp en clair
    return jsonify(cfg)

@api.route('/api/guilds/<guild_id>/config', methods=['POST'])
@require_api_key
def update_guild_config(guild_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    data = request.get_json(silent=True) or {}
    allowed_keys = {"logs_channel", "autorole", "allowed_roles", "safe_roles", "safe_password"}
    updated = {}
    for key, value in data.items():
        if key in allowed_keys:
            update_config(guild_id, key, value)
            updated[key] = value

    if not updated:
        return jsonify({"error": "No valid fields provided"}), 400
    return jsonify({"success": True, "updated": updated})

@api.route('/api/guilds/<guild_id>/lock', methods=['POST'])
@require_api_key
def lock_bot_route(guild_id):
    bot.locked = True
    return jsonify({"success": True, "locked": True})

@api.route('/api/guilds/<guild_id>/unlock', methods=['POST'])
@require_api_key
def unlock_bot_route(guild_id):
    bot.locked = False
    return jsonify({"success": True, "locked": False})

@api.route('/api/guilds/<guild_id>/broadcast', methods=['POST'])
@require_api_key
def broadcast_route(guild_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    data = request.get_json(silent=True) or {}
    message = data.get("message")
    channel_id = data.get("channel_id")
    mention = data.get("mention", "none")

    if not message or not channel_id:
        return jsonify({"error": "message and channel_id are required"}), 400

    channel = guild.get_channel(int(channel_id))
    if not channel:
        return jsonify({"error": "Channel not found"}), 404

    if mention == "everyone":
        ping = "@everyone"
    elif mention == "here":
        ping = "@here"
    else:
        role = discord.utils.get(guild.roles, name=mention)
        ping = role.mention if role else None

    embed = discord.Embed(description=message, color=0x3399ff)
    embed.set_footer(text="📢 Sent from the mobile app")

    async def _send():
        await channel.send(content=ping, embed=embed)

    try:
        run_coroutine(_send())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True})

@api.route('/api/guilds/<guild_id>/members/<user_id>/ban', methods=['POST'])
@require_api_key
def ban_member_route(guild_id, user_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "Banned via mobile app")

    async def _ban():
        member = guild.get_member(int(user_id))
        if not member:
            return False, "Member not found"
        if member.top_role >= guild.me.top_role:
            return False, "Role too high"
        await member.ban(reason=reason)
        return True, None

    try:
        success, error = run_coroutine(_ban())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"success": True})

@api.route('/api/guilds/<guild_id>/members/<user_id>/kick', methods=['POST'])
@require_api_key
def kick_member_route(guild_id, user_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "Kicked via mobile app")

    async def _kick():
        member = guild.get_member(int(user_id))
        if not member:
            return False, "Member not found"
        if member.top_role >= guild.me.top_role:
            return False, "Role too high"
        await member.kick(reason=reason)
        return True, None

    try:
        success, error = run_coroutine(_kick())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"success": True})

@api.route('/api/guilds/<guild_id>/members/<user_id>/warnings', methods=['GET'])
@require_api_key
def get_warnings_route(guild_id, user_id):
    count = get_warns(user_id)
    return jsonify({"user_id": user_id, "warnings": count})

@api.route('/api/guilds/<guild_id>/warnlist', methods=['GET'])
@require_api_key
def warnlist_route(guild_id):
    docs = list(warns_col.find({"count": {"$gt": 0}}))
    result = [{"user_id": d["user_id"], "count": d["count"]} for d in docs]
    return jsonify(result)

@api.route('/api/guilds/<guild_id>/channels', methods=['GET'])
@require_api_key
def list_channels_route(guild_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    channels = [{"id": str(c.id), "name": c.name} for c in guild.text_channels]
    return jsonify(channels)

@api.route('/api/guilds/<guild_id>/roles', methods=['GET'])
@require_api_key
def list_roles_route(guild_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    roles = [{"id": str(r.id), "name": r.name} for r in guild.roles if not r.is_default()]
    return jsonify(roles)

@api.route('/api/guilds/<guild_id>/members', methods=['GET'])
@require_api_key
def list_members_route(guild_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    members = [
        {
            "id": str(m.id),
            "name": m.display_name,
            "username": str(m),
            "avatar_url": m.display_avatar.url,
            "is_muted": m.is_timed_out()
        }
        for m in guild.members if not m.bot
    ]
    return jsonify(members)

@api.route('/api/guilds/<guild_id>/members/<user_id>/mute', methods=['POST'])
@require_api_key
def mute_member_route(guild_id, user_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    data = request.get_json(silent=True) or {}
    minutes = int(data.get("minutes", 10))
    reason = data.get("reason") or "Muted by mobile app"

    async def _mute():
        member = guild.get_member(int(user_id))
        if not member:
            return False, "Member not found"
        if member.top_role >= guild.me.top_role:
            return False, "Role too high"
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        return True, None

    try:
        success, error = run_coroutine(_mute())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"success": True})

@api.route('/api/guilds/<guild_id>/members/<user_id>/unmute', methods=['POST'])
@require_api_key
def unmute_member_route(guild_id, user_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    async def _unmute():
        member = guild.get_member(int(user_id))
        if not member:
            return False, "Member not found"
        await member.timeout(None)
        return True, None

    try:
        success, error = run_coroutine(_unmute())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"success": True})

@api.route('/api/guilds/<guild_id>/members/<user_id>/warn', methods=['POST'])
@require_api_key
def warn_member_route(guild_id, user_id):
    if not bot.is_ready():
        return jsonify({"error": "Bot not ready"}), 503
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    data = request.get_json(silent=True) or {}
    reason = data.get("reason") or "Warned by mobile app"

    member = guild.get_member(int(user_id))
    if not member:
        return jsonify({"error": "Member not found"}), 404

    count = get_warns(user_id) + 1
    set_warns(user_id, count)

    return jsonify({"success": True, "warnings": count, "reason": reason})

@api.route('/api/guilds/<guild_id>/members/<user_id>/unwarn', methods=['POST'])
@require_api_key
def unwarn_member_route(guild_id, user_id):
    count = get_warns(user_id)
    if count == 0:
        return jsonify({"error": "No warnings to remove"}), 400
    count -= 1
    set_warns(user_id, count)
    return jsonify({"success": True, "warnings": count})


def run_api():
    port = int(os.getenv("PORT", 8080))
    api.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_api)
    t.daemon = True
    t.start()

keep_alive()
bot.run(os.getenv("TOKEN"))
