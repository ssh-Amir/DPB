import discord
from discord.ext import commands
import os
import ollama  #For interactions with LLM
import re      #Used for reformatting Str Responses in "summarize_text"

# Create a bot instance with all intents enabled
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# File path for storing data (for your existing commands)
FILE_PATH = "Bot_Storage.txt"

# Ensure the storage file exists
if not os.path.exists(FILE_PATH):
    with open(FILE_PATH, "w") as file:
        file.write("Guild, Username, Group Number\n")
        
def PerformReview(text, model="deepseek-r1:7b", max_length=300):
    """
    Prompts Deepseek-r1 to create a performace review and rating based
    on the text given
    
    """
    try:
        # Ensure text is within the model's processing limit
        truncated_text = text[:max_length]

        # Construct the prompt
        prompt = f"Provide a one hundred word performance review along with a rating from 1-10 based on the following:\n\n{truncated_text}"

        # Send request to Ollama
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        #Packages responses into "full_respond" variable
        full_response = response.get("message", {}).get("content", "").strip()
        
        #Reformats Deepseek response to remove R1 <think> reasoning from expected output
        cleaned_response = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()


        #Returns reformated response with removed <think? reply
        return cleaned_response
        
        
        
       #return response.get("message", {}).get("content", "").strip()'''

    except Exception as e:
        # Log and return error message
        print(f"Error: {e}")
        return "An error occurred while summarizing the text."

@client.command()
async def Perform_Review(ctx):
    """
    Command that asks the user for a 300 word description for the performance review.
    """
    await ctx.send("Please enter your description!")

    def check(m):
        # Only accept messages from the same user and channel that invoked the command
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # Wait for the user's message (with a timeout of 60 seconds)
        user_rev = await client.wait_for("message", timeout=60.0, check=check)
        input_msg = user_rev.content.strip()

        if not input_msg:
            await ctx.send("No text received. Please try again.")
            return

        await ctx.send("Performing Review...")

        # Call the Review helper function to generate the Review.
        review = PerformReview(input_msg)
        await ctx.send(f"**Review:**\n{review}")

    except Exception as e:
        await ctx.send("Timed out or an error occurred. Please try again.")
 
# -------------------------------
# Define a Summary helper function to summarize text using DeepSeek R1 via Ollama
# -------------------------------
#Summarize Text Function
def summarize_text(text):
    """
    This function sends a prompt to DeepSeek R1 (invoked via Ollama)
    asking it to summarize the provided text.
    """
    # Construct the summarization prompt
    prompt = f"Summarize the following text briefly:\n\n{text}"
    
    # Call the model using Ollama's chat function.

    response = ollama.chat(
        model="deepseek-r1:7b",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract and return the generated summary from the response.
    summary = response["message"]["content"].strip()
    return summary
 
 
@client.command()
async def summarize(ctx):
    """
    Command that asks the user for text input and then returns a summarized version
    using deepseek-r1 and Ollama Python library.
    """
    await ctx.send("Please enter the text you would like to summarize:")

    def check(m):
        # Only accept messages from the same user and channel that invoked the command
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # Wait for the user's message (with a timeout of 60 seconds)
        user_message = await client.wait_for("message", timeout=60.0, check=check)
        input_text = user_message.content.strip()

        if not input_text:
            await ctx.send("No text received. Please try again.")
            return

        await ctx.send("Summarizing your text...")

        # Call the helper function to generate the summary.
        summary = summarize_text(input_text)
        await ctx.send(f"**Summary:**\n{summary}")

    except Exception as e:
        await ctx.send("Timed out or an error occurred. Please try again.")


# ------------------------------------------------------------------------------------------
# Discord Bot Events and Commands
# ------------------------------------------------------------------------------------------

@client.event
async def on_ready():
    print("This Bot is awake!")
    print("Use '!commandhelp' for any info") 
    print("------------------")

@client.command()
async def hello(ctx):
    await ctx.send("World!")

@client.command()
async def HiShmeer(ctx):
    await ctx.send("Hello! Happy to see you!")

@client.command()
async def commandhelp(ctx):
    help_text = (
        "List of Commands:\n"
        "!commandhelp: Shows this help message\n"
        "!JoinGroup: Assign your Username and Group #\n"
        "!ShowGroups: Display stored Group and Username information\n"
        "!summarize: Provide text for summarization using DeepSeek R1\n"
        "!Perform_Review: Generates a performance review and rating based on your input!"
    )
    await ctx.send(help_text)

@client.command()
async def JoinGroup(ctx):
    """
    Command to intake a username and group number from the user, then store it in a file.
    """
    await ctx.send("Please enter your username followed by your group number, separated by a space (e.g., 'Amir 2').")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # Wait for the user's response (up to 60 seconds)
        message = await client.wait_for("message", timeout=60.0, check=check)
        content = message.content.split()

        if len(content) == 2:
            username, group_number = content[0], content[1]
            guild_name = ctx.guild.name

            # Append the data to the file
            with open(FILE_PATH, "a") as file:
                file.write(f"{guild_name}, {username}, {group_number}\n")

            await ctx.send(f"Saved: Guild = {guild_name}, Username = {username}, Group Number = {group_number}")
        else:
            await ctx.send("Invalid format. Please use 'username group_number' format.")

    except Exception as e:
        await ctx.send("Timed out or an error occurred. Please try again.")

@client.command()
async def ShowGroups(ctx):
    """
    Command to display the stored data.
    """
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as file:
            data = file.read()
        await ctx.send(f"Stored Data:\n```{data}```")
    else:
        await ctx.send("No data stored yet.")

# Replace 'token' with your actual Discord bot token or use an environment variable.
client.run('')
