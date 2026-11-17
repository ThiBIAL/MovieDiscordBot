import asyncio
import os

import discord
from dotenv import load_dotenv

from weather_bot import getGif, reply

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged in as " + str(self.user.name))
        print("The chatbot Id :: " + str(self.user.id))

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(message.content)

        if not message.content.strip():
            await message.channel.send("Je ne peux lire que du texte pour l'instant 🙂")
            return
        async with message.channel.typing():
            answer = await asyncio.to_thread(reply, message.content)

        weather = answer['weather']
        if weather is None:
            await message.channel.send(answer['text'])
            return

        embed = discord.Embed(
            title=f"Weather in {weather['city']}, {weather['country']}",
            description=answer['text'],
            color=discord.Color.blue(),
        )
        embed.set_image(url=getGif(weather))
        await message.channel.send(embed=embed)

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(TOKEN)
