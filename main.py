import discord
from discord.ext import commands
from discord import app_commands
import flask
from flask import Flask
from threading import Thread

# Keep alive web server
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")

# /ban
@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been banned. Reason: {reason}")

# /kick
@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been kicked. Reason: {reason}")

# /mute
@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int = 10, reason: str = "No reason provided"):
    import datetime
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been muted for {minutes} minutes. Reason: {reason}")

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
    channel = discord.utils.get(message.guild.text_channels, name="logs")
    if channel and not message.author.bot:
        await channel.send(f"🗑️ Message from **{message.author}** deleted: {message.content}")

@bot.event
async def on_message_edit(before, after):
    channel = discord.utils.get(before.guild.text_channels, name="logs")
    if channel and not before.author.bot:
        await channel.send(f"✏️ **{before.author}** edited a message:\n**Before:** {before.content}\n**After:** {after.content}")

keep_alive()
import os
bot.run(os.getenv("TOKEN"))
