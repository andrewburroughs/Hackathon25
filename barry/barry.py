import discord
from discord.ext import commands
import os
from io import BytesIO
import asyncio
import time

# SETTINGS
TOKEN = ""  # Ensure this is the correct token
TARGET_CHANNEL_ID =   # Replace with your channel ID
IMAGE_DIR = "images"
TEMP_DIR = "temp"


# Initialize the bot with only necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable Message Content Intent if needed
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure required directories exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Helper: Download image attachment to memory ---
async def download_image(attachment):
    img_data = await attachment.read()
    return BytesIO(img_data)

# --- !swap command (mocked using pre-saved local images) ---
@bot.command()
async def swap(ctx, target: str):
    # Expects swap images to be named as "swapped_<target>.png"
    filename = f"swapped_{target.lower()}.png"
    image_path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(image_path):
        await ctx.send(f"🧠 Here's your face swapped with `{target}`:", file=discord.File(image_path))
    else:
        await ctx.send(f"❌ No swap result found for `{target}`.\n(Make sure `{filename}` exists in the `images/` folder.)")

@swap.error
async def swap_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!swap <target>`\nPlease provide a target name for the swap command.")
    else:
        await ctx.send("An error occurred while processing the swap command. Please try again.")

# --- !post command: Post image with caption to the target channel ---
@bot.command()
async def post(ctx, *, caption: str = ""):
    if not ctx.message.attachments:
        await ctx.send("📷 Please attach an image to post.")
        return
    image = await download_image(ctx.message.attachments[0])
    target_channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not target_channel:
        await ctx.send("❌ Could not find the target channel.")
        return
    file = discord.File(fp=image, filename="post.png")
    embed = discord.Embed(description=caption, color=0x00ffcc)
    embed.set_image(url="attachment://post.png")
    embed.set_footer(text=f"Posted by {ctx.author.display_name}")
    await target_channel.send(embed=embed, file=file)
    await ctx.send("✅ Posted successfully to the feed!")

@post.error
async def post_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!post <caption>` with an attached image.\nPlease provide a caption and attach an image.")
    else:
        await ctx.send("An error occurred while processing the post command. Please try again.")

# --- !local command: Send a local image from disk ---
@bot.command()
async def local(ctx, name: str):
    # Looks for a file named "<name>.png" in the images folder
    filename = f"{name.lower()}.png"
    image_path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(image_path):
        await ctx.send(f"📂 Sending local image: `{filename}`", file=discord.File(image_path))
    else:
        await ctx.send(f"❌ Image `{filename}` not found in the `images/` folder.")

@local.error
async def local_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!local <name>`\nPlease provide the name of the image.")
    else:
        await ctx.send("An error occurred while processing the local command. Please try again.")

@bot.command(name="list")
async def list_images(ctx):
    # List all files ending with ".png" in the images folder
    files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")]
    if files:
        # Optionally, remove the extension for readability
        available = [os.path.splitext(f)[0] for f in files]
        await ctx.send("Available images: " + ", ".join(available))
    else:
        await ctx.send("No PNG images found in the images folder.")


@list_images.error
async def list_error(ctx, error):
    await ctx.send("An error occurred while listing images. Please try again.")

# --- Global error handler for commands not caught individually ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("That command doesn't exist. Use `!help` to see available commands.")
    else:
        # If a command-specific error handler exists, it will take precedence.
        pass

# --- on_message event for responding to "cookie" ---
@bot.event
async def on_message(message):
    # Ignore messages from bots to prevent loops
    if message.author.bot:
        return

    if message.content.lower() == "cookie":
        await message.channel.send(":cookie:")

    # Process commands after custom events
    await bot.process_commands(message)



# Run the bot
bot.run(TOKEN)