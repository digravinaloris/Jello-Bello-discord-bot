import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
from threading import Thread
import asyncio
import datetime

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

@bot.event
async def on_ready():
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
        await interaction.response.send_message("❌ I can't ban this member, their role is too high.", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been banned. Reason: {reason}")

# /kick
@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I can't kick this member, their role is too high.", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been kicked. Reason: {reason}")

# /mute
@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int = 10, reason: str = "No reason provided"):
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I can't mute this member, their role is too high.", ephemeral=True)
        return
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been muted for {minutes} minutes. Reason: {reason}")

# /unmute
@bot.tree.command(name="unmute", description="Remove timeout from a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I can't unmute this member, their role is too high.", ephemeral=True)
        return
    await member.timeout(None)
    await interaction.response.send_message(f"✅ **{member}** has been unmuted.")

# /unban
@bot.tree.command(name="unban", description="Unban a user by ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ **{user}** has been unbanned.")
    except:
        await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)

# /warn
warns = {}
@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    uid = str(member.id)
    warns[uid] = warns.get(uid, 0) + 1
    await interaction.response.send_message(f"⚠️ **{member}** has been warned. Reason: {reason} (Total warns: {warns[uid]})")

# /warnings
@bot.tree.command(name="warnings", description="Check warnings of a member")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    uid = str(member.id)
    count = warns.get(uid, 0)
    await interaction.response.send_message(f"⚠️ **{member}** has **{count}** warning(s).")

# /clear
@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 10):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🗑️ Cleared {amount} messages.", ephemeral=True)

# Logs
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="logs")
    if channel:
        await channel.send(f"✅ **{member}** joined the server.")

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="logs")
    if channel:
        await channel.send(f"❌ **{member}** left the server.")

@bot.event
async def on_message_delete(message):
    if message.guild is None or message.author.bot:
        return
    channel = discord.utils.get(message.guild.text_channels, name="logs")
    if channel:
        await channel.send(f"🗑️ Message from **{message.author}** deleted: {message.content}")

@bot.event
async def on_message_edit(before, after):
    if before.guild is None or before.author.bot:
        return
    channel = discord.utils.get(before.guild.text_channels, name="logs")
    if channel:
        await channel.send(f"✏️ **{before.author}** edited a message:\n**Before:** {before.content}\n**After:** {after.content}")

keep_alive()
bot.run(os.getenv("TOKEN"))
    
