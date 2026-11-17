"""MovieBot Discord : Discord -> Rasa NLU -> TheMovieDB -> Discord.

À lancer avec l'environnement rasa_env (Python 3.9) :
    C:\\Users\\tibob\\rasa_env\\Scripts\\Activate.ps1
    python bot.py
(La version météo de la partie 1 est dans bot_weather.py.)
"""
import os

import discord
from dotenv import load_dotenv

from movie_bot import reply  # charge aussi le modèle Rasa (quelques secondes)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN is missing: check your .env file")


def to_discord(answer):
    """Transforme le dict renvoyé par movie_bot.reply en arguments pour send()/reply()."""
    if 'title' not in answer:
        return {'content': answer['text']}

    embed = discord.Embed(title=answer['title'], url=answer.get('url'),
                          description=answer['text'], color=answer.get('color', 0x01B4E4))
    for name, value in answer.get('fields', []):
        embed.add_field(name=name, value=value, inline=True)
    if answer.get('thumbnail'):
        embed.set_thumbnail(url=answer['thumbnail'])
    if answer.get('image'):
        embed.set_image(url=answer['image'])
    embed.set_footer(text="Data from TheMovieDB")
    return {'embed': embed}


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged in as " + str(self.user.name))
        print("The chatbot Id :: " + str(self.user.id))
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="movies 🍿 | type help"))

    async def on_message(self, message):
        if message.author == self.user or message.author.bot:
            return

        # Message sans texte (image seule, fichier, sticker...) : rien à analyser
        if not message.content.strip():
            await message.reply("I can only read text for now 🙂")
            return

        async with message.channel.typing():
            answer = await reply(message.content, message.author.id, message.author.display_name)

        # message.reply : réponse "citée" sous le message de l'utilisateur
        await message.reply(**to_discord(answer), mention_author=False)


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(TOKEN)
