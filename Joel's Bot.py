import discord
from discord.ext import commands
import os
import requests
import json
import sqlite3
import subprocess
import glob
from pytube import YouTube
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN is missing!")

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Discord message limit
DISCORD_MESSAGE_LIMIT = 2000

# Local DeepSeek R1 via Ollama
def ask_ollama(user_message):
    url = "http://localhost:11434/api/generate"
    data = {"model": "deepseek-r1:1.5b", "prompt": user_message, "stream": False}

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            full_response = response.json().get("response", "No response received.")
            return [full_response[i : i + DISCORD_MESSAGE_LIMIT] for i in range(0, len(full_response), DISCORD_MESSAGE_LIMIT)]
        return [f"Error: {response.status_code} - {response.text}"]
    except requests.exceptions.RequestException as e:
        return [f"Request failed: {e}"]

# Feedback database setup
conn = sqlite3.connect("feedback.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS feedback (user_id TEXT, username TEXT, message TEXT)")
conn.commit()

# Bot Ready Event
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Ping Command
@bot.command()
async def ping(ctx):
    await ctx.send("pong!")

# Save User Thoughts
@bot.command()
async def thoughts(ctx, *, thought: str):
    with open("thoughts.txt", "a") as file:
        file.write(f"user {ctx.author}: {thought}\n")
    await ctx.send(f"Your thought has been saved, {ctx.author}!")

# Summarize User Thoughts using DeepSeek API
@bot.command()
async def opinions(ctx, *, username: str):
    user_thoughts = []
    with open("thoughts.txt", "r") as file:
        user_thoughts = [line.strip() for line in file if f"user {username}:" in line]

    if not user_thoughts:
        await ctx.send(f"No thoughts found for {username}.")
        return

    thoughts_text = "\n".join(user_thoughts)
    prompt = f"For user {username}, summarize their opinions in 20 words or less: {thoughts_text}"
    
    data = {"model": "deepseek-r1:1.5b", "prompt": prompt, "stream": False}
    response = requests.post("http://localhost:11434/api/generate", json=data)

    if response.status_code == 200:
        summary = response.json().get("response", "Error generating summary.")
        with open("LLMthoughts.txt", "a") as summary_file:
            summary_file.write(f"Summary for {username}:\n{summary}\n\n")
        await ctx.send(f"Summary of {username}'s thoughts:\n{summary}")
    else:
        await ctx.send("Error summarizing the thoughts.")

# Ask DeepSeek LLM
@bot.command(name="ask")
async def ask(ctx, *, user_message: str):
    responses = ask_ollama(user_message)
    for response in responses:
        await ctx.send(response)

# Detect Large YouTube Videos & Remove Shorts Embeds
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Remove YouTube Shorts embeds
    if 'shorts' in message.content.lower():
        await message.channel.send(f"Hi {message.author.mention}, Morgi doesn't like 'shorts'!")
        for embed in message.embeds:
            embed.url = None
            await message.edit(embed=embed)

        # YouTube Download Handling
        shortURL = message.content
        directory = "/root/ytshortsbot/FileCache/"
        os.chdir(directory)
        result = subprocess.run(['/root/ytshortsbot/venv/bin/yt-dlp', shortURL], capture_output=True, text=True)

        if result.returncode == 0:
            vidFiles = glob.glob(os.path.join(directory, "*"))
            video_path = vidFiles[0]

            # Check if video file size is under 25MB before sending
            if os.path.getsize(video_path) > 25 * 1024 * 1024:
                await message.channel.send("Error: Video file is larger than 25MB and cannot be sent.")
            else:
                await message.channel.send(file=discord.File(video_path))

            # Cleanup sent file
            if os.path.exists(video_path):
                os.remove(video_path)
        else:
            await message.channel.send("Error downloading YouTube Shorts video.")

    await bot.process_commands(message)

# Run Bot
bot.run(DISCORD_BOT_TOKEN)
