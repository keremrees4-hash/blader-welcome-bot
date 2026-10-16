import os
import io
import json
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_FILE = "welcome_config.json"
BACKGROUND_FILE = "background.png"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()

async def make_welcome_card(member):
    width, height = 1100, 520
    background = Image.open(BACKGROUND_FILE).convert("RGB")
    # Crop to a wide banner and resize.
    ratio = max(width / background.width, height / background.height)
    background = background.resize((int(background.width * ratio), int(background.height * ratio)), Image.Resampling.LANCZOS)
    left = (background.width - width) // 2
    top = (background.height - height) // 2
    background = background.crop((left, top, left + width, top + height)).filter(ImageFilter.GaussianBlur(1.2))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 65))
    card = Image.alpha_composite(background.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(card)

    # Subtle frame
    draw.rounded_rectangle((14, 14, width-14, height-14), radius=24, outline=(255,255,255,220), width=3)

    async with aiohttp.ClientSession() as session:
        async with session.get(member.display_avatar.replace(size=256, format="png").url) as response:
            avatar_bytes = await response.read()
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((190, 190), Image.Resampling.LANCZOS)
    mask = Image.new("L", avatar.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 189, 189), fill=255)
    avatar.putalpha(mask)

    # Avatar border and shadow
    center_x, avatar_y = width // 2, 85
    draw.ellipse((center_x-101, avatar_y-6, center_x+101, avatar_y+196), fill=(0,0,0,130))
    draw.ellipse((center_x-99, avatar_y-4, center_x+99, avatar_y+194), outline=(255,255,255,240), width=5)
    card.alpha_composite(avatar, (center_x-95, avatar_y))

    title = f"Hoş Geldin {member.display_name}!"
    title_font = get_font(43, True)
    # Keep long names inside the banner.
    while draw.textbbox((0,0), title, font=title_font, stroke_width=2)[2] > width - 80 and getattr(title_font, "size", 43) > 24:
        title_font = get_font(title_font.size - 2, True)
    bbox = draw.textbbox((0,0), title, font=title_font, stroke_width=2)
    title_w = bbox[2] - bbox[0]
    title_y = 315
    draw.text(((width-title_w)//2, title_y), title, font=title_font, fill="white",
              stroke_width=3, stroke_fill=(0,0,0,220))

    member_count = f"#{member.guild.member_count}"
    count_font = get_font(28, False)
    count_w = draw.textbbox((0,0), member_count, font=count_font)[2]
    draw.text(((width-count_w)//2, 385), member_count, font=count_font, fill=(245,245,245),
              stroke_width=2, stroke_fill=(0,0,0,200))

    out = io.BytesIO()
    card.convert("RGB").save(out, format="PNG")
    out.seek(0)
    return out

@bot.event
async def on_ready():
    print(f"Bot hazır: {bot.user} (ID: {bot.user.id})")

@bot.command(name="welcome-message-open")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def welcome_open(ctx):
    config = load_config()
    config[str(ctx.guild.id)] = ctx.channel.id
    save_config(config)
    await ctx.reply(f"Hoş geldin mesajları bu kanalda açıldı: {ctx.channel.mention}", mention_author=False)

@bot.command(name="welcome-message-close")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def welcome_close(ctx):
    config = load_config()
    config.pop(str(ctx.guild.id), None)
    save_config(config)
    await ctx.reply("Hoş geldin mesajları kapatıldı.", mention_author=False)

@bot.event
async def on_member_join(member):
    config = load_config()
    channel_id = config.get(str(member.guild.id))
    if not channel_id:
        return
    channel = member.guild.get_channel(int(channel_id))
    if channel is None:
        return
    try:
        image_file = await make_welcome_card(member)
        await channel.send(
            content=f"Hoş geldin {member.mention}! Sunucumuza katıldığın için sevindik.",
            file=discord.File(image_file, filename="welcome.png")
        )
    except Exception as error:
        print(f"Welcome kartı oluşturulamadı: {error}")

@welcome_open.error
@welcome_close.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Bu komutu kullanmak için Sunucuyu Yönet yetkisi gerekiyor.", mention_author=False)
    else:
        await ctx.reply("Komut çalışmadı. Bot izinlerini ve Railway loglarını kontrol et.", mention_author=False)
        print(f"Komut hatası: {error}")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN ortam değişkeni ayarlanmamış.")
bot.run(TOKEN)
