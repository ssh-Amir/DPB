#TODO: 
#DELETE emmbed from shorts links it processes, 
#detect if video filesize will be larger than 25MB

import requests
import json
#stuff below for discord 
import subprocess
import glob
import os
import discord
from pytube import YouTube
from discord.ext import commands
#LLM deepseek openrouter L1 api key
api_key = ""
#url to openrouter api
url = "https://openrouter.ai/api/v1/chat/completions"
#set authorization token headers etc
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
# Create an instance of the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command: Responds with "Pong!" when the user types "!ping"
@bot.command()
async def ping(ctx):
    await ctx.send("pong!")
    
#event: listen for thoughts command and input whatever sentence is after that
#into thoughts.txt file under the user of whoever did the command
@bot.command()
async def thoughts(ctx,*,thought:str):
    #open a file and append user thoughts
    with open("thoughts.txt","a") as file:
        file.write(f"user {ctx.author}: {thought}\n")
    await ctx.send(f"your thought has been saved, {ctx.author}!")

#event: listen for !opinions command and it will take User: @user as an option 
#then llm will compile all thoughts by that user in thoughts.txt to summarize it. LLM summarization
#will also be added to its own file LLMthoughts.txt 
@bot.command()
async def opinions(ctx,*,username:str):
    user_thoughts = []
    with open("thoughts.txt","r") as file:
        for line in file:
            if f"user {username}:" in line:
                user_thoughts.append(line.strip())


    if not user_thoughts:
        await ctx.send(f"No thoughts found for {username}.")
        return

    thoughts_text = "\n".join(user_thoughts)

    prompt = f"FOr user {username}, summarize their opinions in 20 words or less: {thoughts_text}"
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }       

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        summary = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        with open("LLMthoughts.txt", "a") as summary_file:
            summary_file.write(f"Summary for {username}:\n{summary}\n\n")
        await ctx.send(f"Summary of {username}'s thoughts:\n{summary}")

    else:
        await ctx.send("Sorry, there was an error with summarizing the thoughts.")
    
    # Event: Listen for messages containing certain text
@bot.event
async def on_message(message):
    # Ignore the bot's own messages
	if message.author == bot.user:
		return
    
    # Check if the message contains the word "shorts"
	if 'shorts' in message.content:  # Lowercase to make it case-insensitive
		await message.channel.send(f"Hi {message.author.mention}, morgi doesn't like 'shorts'!")
		#remove embeds for youtube shorts links
	for embed in message.embeds:
		if embed.url.startswith("https://discordapp.com/channels/"):
			embed.url = None
			await message.edit(embed=embed)
        #download youtube shorts link into local file through calling bash
		#run youtubedl and download using link to folder filecache
		directory = '/root/ytshortsbot/FileCache/'
		shortURL = message.content
		#change youtube dl directory execution
		os.chdir(directory)
		result = subprocess.run(['/root/ytshortsbot/venv/bin/yt-dlp', shortURL], capture_output=True, text=True)
		if result.returncode == 0:
				#look for and send file over discord
				file_path= '/root/ytshortsbot/FileCache/'
				vidFiles = glob.glob(os.path.join(file_path, "*"))
				
				await message.channel.send(file=discord.File(vidFiles[0]))
				#delete previous file once sent if it exists
				if os.path.exists(vidFiles[0]):
					os.remove(vidFiles[0])
					#await message.channel.send(f"The file {file_path} has been deleted.")
				else:
					await message.channel.send(f"Error: The file {file_path} does not exist.")
			
			
		#output std.out of youtubedl output
		#await message.channel.send(f"Output: {result.stdout}")  # prints: comand output
		print("Return code:", result.returncode)  # prints: 0 (successful execution)
	
    # This is important to ensure commands still work
	await bot.process_commands(message)

    
    

# discord token
bot.run('')
