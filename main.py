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
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
BUTTON_CHANNEL_ID = int(os.getenv("VERIFY_CHANNEL_ID")) 
GUILD_ID = int(os.getenv("GUILD_ID"))  # サーバーID
ROLE_ID = int(os.getenv("ROLE_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', help_command=None, intents=intents)


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

@bot.command(name='loadstring')
async def loadstring_command(ctx, url: str = None):
    if not url:
        await ctx.send("❌ Usage: `!loadstring <URL>` – Please provide a valid URL.")
        return

    if not url.startswith("http"):
        await ctx.send("❌ Invalid URL. Make sure it starts with 'http'.")
        return

    lua_code = f'```lua\nloadstring(game:HttpGet("{url}"))()\n```'
    await ctx.send(lua_code)

@bot.command(name="info")
async def info_command(ctx):
    embed = discord.Embed(title="📜 Command List", color=discord.Color.green())
    embed.add_field(name="!loadstring <url>", value="Converts a URL into a Roblox loadstring.", inline=False)
    embed.add_field(name="!shutdown", value="Shuts down the bot (owner only).", inline=False)
    embed.add_field(name="!info", value="Shows this help message.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="help")  # ❌ これを削除または無効化
async def help_command(ctx):
    ...
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"Welcome to the server, {member.mention}!")

# 認証ボタンのUIクラス
class AuthButtonView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # ボタンが永遠に表示されるように
        self.bot = bot

    @ui.button(label="Click to Verify", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ボタンを押したユーザー
        member = interaction.user
        
        # サーバーとロールを取得
        guild = bot.get_guild(GUILD_ID)
        role = guild.get_role(ROLE_ID)
        
        if guild and role:
            # ユーザーにロールを付与
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ {member.mention} has been verified and the role has been assigned!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Unable to assign the role. Please check the server and role configuration.", ephemeral=True)

# Botイベント: ボットがオンラインになったとき
@bot.event
async def on_ready():
    print(f"{bot.user} has logged in.")
    channel = bot.get_channel(BUTTON_CHANNEL_ID)
    
    if channel:
        # 認証ボタンを送信
        embed = discord.Embed(title="Please click the button below to verify yourself.", color=0x00ff00)
        await channel.send(embed=embed, view=AuthButtonView())
    else:
        print("Channel not found.")


# Run the bot
bot.run(TOKEN)
