import os
import discord
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv
import time

from keep_alive import keep_alive

keep_alive()  

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID"))
BUTTON_CHANNEL_ID = int(os.getenv("BUTTON_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True  # For message delete event
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def shutdown(ctx):
    """Shuts down the bot."""
    # Check if the user has the necessary permissions to shut down the bot
    if ctx.author.id == 1290952054872739892:  # Replace YOUR_USER_ID with your Discord user ID
        await ctx.send("Shutting down...")
        await bot.close()  # Gracefully shuts down the bot
        sys.exit(0)  # Exit the program cleanly
    else:
        await ctx.send("You do not have permission to shut down the bot.")


status_options = {
    "working": "｛🟢｝WORKING",
    "update": "｛🟡｝UPDATE",
    "down": "｛🔴｝DOWN",
    "coming_soon": "｛🔵｝COMING SOON"
}

class StatusButtonView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Keep buttons visible
        self.bot = bot

    @ui.button(label="🟢 WORKING", style=discord.ButtonStyle.success, custom_id="status_working")
    async def working(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_status(interaction, "working")

    @ui.button(label="🟡 UPDATE", style=discord.ButtonStyle.primary, custom_id="status_update")
    async def update(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_status(interaction, "update")

    @ui.button(label="🔴 DOWN", style=discord.ButtonStyle.danger, custom_id="status_down")
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_status(interaction, "down")

    @ui.button(label="🔵 COMING SOON", style=discord.ButtonStyle.secondary, custom_id="status_coming_soon")
    async def coming_soon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_status(interaction, "coming_soon")

    async def change_status(self, interaction: discord.Interaction, status_key: str):
        # Respond to the interaction
        await interaction.response.defer()
        
        try:
            channel = bot.get_channel(STATUS_CHANNEL_ID)
            if channel:
                if channel.name != status_options[status_key]:  # Change only if name is different
                    await channel.edit(name=status_options[status_key])
                    await interaction.followup.send(
                        f"✅ Script status has been changed to {status_options[status_key]}.", ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ The status is already {status_options[status_key]}. No change needed.", ephemeral=True
                    )
        except discord.errors.HTTPException as e:
            if e.response.status == 429:  # Rate limit error
                reset_time = float(e.response.headers['X-RateLimit-Reset'])  # Get reset time
                wait_time = reset_time - time.time() + 1  # Add 1 second buffer
                print(f"Rate limit reached. Retrying in {wait_time} seconds.")
                await interaction.followup.send(
                    "❌ Rate limit reached. Please try again later.", ephemeral=True
                )
                time.sleep(wait_time)  # Wait for the reset time
                await self.change_status(interaction, status_key)  # Retry

# Bot event when ready
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="cooked ftap"))
    print(f"{bot.user} has logged in.")
    await send_button_message_if_missing()  # Send message if it's missing on startup


# Resend the message if it is deleted
@bot.event
async def on_message_delete(message):
    if message.channel.id == BUTTON_CHANNEL_ID and message.author == bot.user and message.components:
        print("⚠️ Button message deleted. Resending.")
        await send_button_message()


async def send_button_message():
    channel = bot.get_channel(BUTTON_CHANNEL_ID)

    # チャンネル内のメッセージを全削除（自身のメッセージも含む）
    def is_deletable(message):
        return True  # 全メッセージ対象にする

    deleted = await channel.purge(limit=None, check=is_deletable)
    print(f"🗑️ {len(deleted)} 件のメッセージを削除しました。")

    # 新しい埋め込みとボタンを送信
    embed = discord.Embed(
        title="🔧 Script Status Change",
        description="Click the buttons below to change the script status.",
        color=0x00ffcc
    )
    await channel.send(embed=embed, view=StatusButtonView())




# Send button message if it's missing
async def send_button_message_if_missing():
    channel = bot.get_channel(BUTTON_CHANNEL_ID)
    async for message in channel.history(limit=20):
        if message.author == bot.user and message.components:
            return
    await send_button_message()


# Run the bot
bot.run(TOKEN)
