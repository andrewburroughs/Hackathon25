import discord
from discord.ext import commands
import os
from io import BytesIO
import datetime
from PIL import Image  # Requires Pillow (install via: pip install pillow)

# SETTINGS
TOKEN = ""  # Enter your bot token here
TARGET_CHANNEL_ID = 1358165647946940509  # Replace with your target channel ID (as an integer)
IMAGE_DIR = "images"
TEMP_DIR = "temp"


# Initialize the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable Message Content Intent if needed
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure required directories exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Helper function: Dummy face swap using a vertical half-split ---
def swap_faces(image1, image2):
    # Resize image2 to match image1's size
    image2 = image2.resize(image1.size)
    w, h = image1.size
    # Create a new image by taking the left half from image2 and the right half from image1
    swapped = Image.new('RGB', (w, h))
    swapped.paste(image2.crop((0, 0, w // 2, h)), (0, 0))
    swapped.paste(image1.crop((w // 2, 0, w, h)), (w // 2, 0))
    return swapped

# --- !list command: List all PNG images in the images folder (names without extension) ---
@bot.command(name="list")
async def list_images(ctx):
    files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")]
    if files:
        available = [os.path.splitext(f)[0] for f in files]
        await ctx.send("Available images: " + ", ".join(available))
    else:
        await ctx.send("No PNG images found in the images folder.")

@list_images.error
async def list_error(ctx, error):
    await ctx.send("An error occurred while listing images. Please try again.")

# Helper to get the target channel (tries cache first, then fetches if needed)
async def get_target_channel():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
        except Exception as e:
            print("Error fetching channel:", e)
            return None
    return channel

# --- !swap command: Swap faces between two images from the images folder ---
@bot.command()
async def swap(ctx, first: str, second: str):
    # Append .png if not provided by the user
    if not first.lower().endswith(".png"):
        first = first + ".png"
    if not second.lower().endswith(".png"):
        second = second + ".png"
    
    path1 = os.path.join(IMAGE_DIR, first.lower())
    path2 = os.path.join(IMAGE_DIR, second.lower())
    
    if not os.path.exists(path1):
        await ctx.send(f"❌ Image `{first}` not found in the images folder.")
        return
    if not os.path.exists(path2):
        await ctx.send(f"❌ Image `{second}` not found in the images folder.")
        return
    
    try:
        image1 = Image.open(path1).convert("RGB")
        image2 = Image.open(path2).convert("RGB")
        swapped_image = swap_faces(image1, image2)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"swapped_{timestamp}.png"
        image_path = os.path.join(IMAGE_DIR, filename)
        # Save the swapped image to disk
        swapped_image.save(image_path)
        # Retrieve the target channel
        target_channel = await get_target_channel()
        if target_channel:
            # Now read the saved image from disk and send it (similar to !local)
            await target_channel.send(f"🧠 Face swap complete! Stored as `{filename}`.", 
                                    file=discord.File(image_path))
            # Optionally, send a message to the original channel
            image_path = os.path.join(IMAGE_DIR, filename)
            if os.path.exists(image_path):
                await ctx.send(f"📂 Sending local image: `{filename}`", file=discord.File(image_path))
                                      
            await ctx.send("✅ Swapped image posted to the target channel.")
        else:
            await ctx.send("❌ Could not find the target channel.")
    except Exception as e:
        await ctx.send("An error occurred while processing the face swap. Please try again.")
        print(e)

@swap.error
async def swap_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!swap <image1> <image2>`\nPlease provide the names of the two images to swap faces from.")
    else:
        await ctx.send("An error occurred with the swap command. Please try again.")

# --- !local command: Send a local image from disk ---
@bot.command()
async def local(ctx, name: str):
    # Looks for a file named "<name>.png" in the images folder
    filename = f"{name.lower()}.png"
    image_path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(image_path):
        await ctx.send(f"📂 Sending local image: `{filename}`", file=discord.File(image_path))
    else:
        await ctx.send(f"❌ Image `{filename}` not found in the images folder.")

@local.error
async def local_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!local <name>`\nPlease provide the name of the image.")
    else:
        await ctx.send("An error occurred while processing the local command. Please try again.")

# --- Global error handler for unknown commands ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("That command doesn't exist. Use `!help` to see available commands.")
    else:
        pass

# --- on_message event for extra responses (e.g., "cookie") ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower() == "cookie":
        await message.channel.send(":cookie:")
    await bot.process_commands(message)

# Run the bot
bot.run(TOKEN)
