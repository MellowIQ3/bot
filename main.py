import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"{bot.user} ")

    await bot.change_presence(activity=discord.Game(name="cooked ftap"))


bot.run(TOKEN)
