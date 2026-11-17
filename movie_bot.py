"""Logique du MovieBot : Rasa NLU (intent + entités) -> TheMovieDB -> réponse.

reply() renvoie un dict décrivant la réponse, que bot.py transforme en message Discord :
    {'text': str,                       # toujours présent
     'title', 'url', 'thumbnail',       # optionnels -> embed
     'image', 'fields', 'color'}
"""
import asyncio
import random
import re
from datetime import date

import movie_api as api
from nlu import parse_async

# Entité indispensable pour chaque intent "métier"
REQUIRED = {
    'movieinfo': 'movie', 'director': 'movie', 'releaseYear': 'movie',
    'actors': 'movie', 'poster': 'movie', 'rating': 'movie',
    'filmography': 'person',
}
SMALL_TALK = {'greet', 'goodbye', 'thanks', 'help'}

# Mémoire courte par utilisateur :
#   'movie'   : dernier film dont on a parlé -> "who directed it?" fonctionne
#   'pending' : intent en attente d'une entité -> le bot a demandé "Which movie?"
context = {}

COLORS = {'movieinfo': 0x01B4E4, 'director': 0x9B59B6, 'releaseYear': 0x2ECC71,
          'actors': 0xE67E22, 'poster': 0x90CEA1, 'rating': 0xF1C40F, 'filmography': 0xE91E63}


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
async def reply(text, user_id, user_name):
    intent, confidence, entities = await parse_async(text)
    print(f"[NLU] {text!r} -> {intent} ({confidence:.2f}) {entities}")
    ctx = context.setdefault(user_id, {'movie': None, 'pending': None})

    # 1) Le bot attendait une réponse à "Which movie?" / "Which person?"
    if ctx['pending'] and _is_answer_to_pending(text, intent, entities, ctx['pending']):
        slot = REQUIRED[ctx['pending']]
        entities = {slot: entities.get(slot) or text.strip()}
        intent = ctx['pending']
    ctx['pending'] = None

    # Message = juste un titre ("interstellar") -> fiche du film, même si l'intent est incertain
    if entities.get('movie') and _norm(entities['movie']) == _norm(text):
        intent = 'movieinfo'

    # 2) Small talk / incompréhension
    if intent == 'greet':
        return {'text': f"Hello {user_name}! 👋 I'm **MovieBot** 🎬\n"
                        "Ask me anything about a movie: plot, director, cast, release date, "
                        "rating or poster. Type **help** to see examples."}
    if intent == 'goodbye':
        return {'text': random.choice([f"Bye {user_name}, enjoy your next movie! 🍿",
                                       f"See you soon {user_name}! 🎬"])}
    if intent == 'thanks':
        return {'text': random.choice(["You're welcome! 😊", "Anytime! 🍿", "My pleasure 🎬"])}
    if intent == 'help':
        return _help()
    if intent == 'out_of_scope':
        return {'text': f"Sorry {user_name}, I only know about movies 🎬 "
                        "Try *who directed Inception?* or type **help**."}
    if intent not in REQUIRED:  # 'unclear' ou intent inconnu
        return {'text': f"Hmm, I'm not sure I understood, {user_name} 🤔 Could you rephrase? "
                        "(type **help** for examples)"}

    # 3) Vérifier l'entité indispensable
    slot = REQUIRED[intent]
    value = entities.get(slot)
    if not value and slot == 'movie' and ctx['movie'] and _refers_to_context(text):
        value = ctx['movie']          # "who directed it?" -> dernier film évoqué
    if not value:
        ctx['pending'] = intent
        return {'text': "Which movie are you talking about? 🎬" if slot == 'movie'
                else "Which director or actor are you talking about? 🎭"}

    # 4) Interroger TMDB (requests est bloquant -> thread séparé)
    try:
        if slot == 'movie':
            return await asyncio.to_thread(_movie_answer, intent, value, ctx)
        return await asyncio.to_thread(_person_answer, value)
    except api.TMDBError as e:
        return {'text': f"⚠️ {e}"}


CONTEXT_WORDS = re.compile(r"\b(it|its|it's|this|that|the movie|the film|this one|same)\b", re.I)


def _refers_to_context(text):
    """'who directed it?' ou 'who directed' -> oui ; 'tell me about xqzzzvv' -> non
    (un titre inconnu que Rasa n'a pas extrait : on ne doit pas répondre sur l'ancien film)."""
    return bool(CONTEXT_WORDS.search(text)) or len(text.split()) <= 2


def _norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def _is_answer_to_pending(text, intent, entities, pending):
    """Le message répond-il à la question posée, ou est-ce une nouvelle demande ?"""
    """Le bot a demandé "Which movie?" : ce message est-il la réponse, ou une nouvelle demande ?
        "inception"                  -> réponse (même si Rasa le classe 'rating')
        "xqzzzvv" (titre inconnu)    -> réponse (texte brut)
        "when was Titanic released"  -> nouvelle question
        "who starred" / "thanks"     -> nouvelle demande"""
    if intent in SMALL_TALK:
        return False
    found = entities.get(REQUIRED[pending])
    if found and _norm(found) == _norm(text):
        return True                     # le message est juste le titre / le nom
    if intent in REQUIRED and intent != pending:
        return False                    # autre question complète
    return True


# ---------------------------------------------------------------------------
# Réponses "film"
# ---------------------------------------------------------------------------
def _movie_answer(intent, title, ctx):
    movie_id = api.search_movie(title)
    if movie_id is None:
        return {'text': f"I couldn't find any movie called **{title}** 🤔 Check the spelling?"}
    m = api.get_movie(movie_id)
    ctx['movie'] = m['title']

    base = {'title': f"{m['title']} ({m['year']})", 'url': m['url'],
            'thumbnail': m['poster'], 'color': COLORS[intent]}
    name = f"**{m['title']}**"

    if intent == 'movieinfo':
        text = (f"*{m['tagline']}*\n\n" if m['tagline'] else "") + m['overview']
        fields = [("🎬 Director", ", ".join(m['directors']) or "Unknown"),
                  ("🎭 Genres", ", ".join(m['genres']) or "Unknown"),
                  ("⏱️ Runtime", _runtime(m['runtime'])),
                  ("⭐ Rating", f"{m['rating']:.1f}/10")]
        return {**base, 'text': text, 'fields': fields}

    if intent == 'director':
        if not m['directors']:
            return {**base, 'text': f"I don't know who directed {name} 🤷"}
        who = " and ".join(f"**{d}**" for d in m['directors'])
        return {**base, 'text': f"{name} was directed by {who} 🎬"}

    if intent == 'releaseYear':
        if not m['release_date']:
            return {**base, 'text': f"{name} has no release date yet 📅"}
        d = date.fromisoformat(m['release_date'])
        years = date.today().year - d.year
        when = (f"that's **{years} years ago**" if years > 1 else
                "last year" if years == 1 else "this year" if d <= date.today() else "coming soon!")
        return {**base, 'text': f"{name} was released on **{d:%B %d, %Y}**, {when} 📅"}

    if intent == 'actors':
        if not m['cast']:
            return {**base, 'text': f"I don't have the cast of {name} 🤷"}
        lines = "\n".join(f"• **{a}**" + (f" as *{c}*" if c else "") for a, c in m['cast'])
        return {**base, 'text': f"The main cast of {name} 🎭\n{lines}"}

    if intent == 'rating':
        r = m['rating']
        verdict = ("a masterpiece! 🏆" if r >= 8 else "really good 👍" if r >= 7 else
                   "decent 🙂" if r >= 6 else "rather disappointing 😕")
        stars = "★" * round(r / 2) + "☆" * (5 - round(r / 2))
        return {**base, 'text': f"{name} is rated **{r:.1f}/10** {stars}\n"
                                f"({m['votes']:,} votes on TMDB), people find it {verdict}"}

    if intent == 'poster':
        if not m['poster']:
            return {**base, 'text': f"I couldn't find a poster for {name} 🖼️"}
        return {**base, 'thumbnail': None, 'image': m['poster'],
                'text': f"Here is the poster of {name} 🖼️"}


def _runtime(minutes):
    return f"{minutes // 60}h{minutes % 60:02d}" if minutes else "Unknown"


# ---------------------------------------------------------------------------
# Réponse "personne"
# ---------------------------------------------------------------------------
def _person_answer(name):
    p = api.search_person(name)
    if p is None:
        return {'text': f"I couldn't find anyone called **{name}** 🤔"}
    movies = api.get_filmography(p)
    if not movies:
        return {'text': f"I don't know any movie by **{p['name']}** 🤷"}
    role = "directed" if p['department'] == 'Directing' else "starred in"
    lines = "\n".join(f"• {t} ({y})" for t, y in movies)
    return {'title': p['name'], 'url': p['url'], 'thumbnail': p['photo'],
            'color': COLORS['filmography'],
            'text': f"Famous movies {p['name']} {role} 🎞️\n{lines}"}


def _help():
    return {'title': "What can I do? 🎬", 'color': 0x01B4E4,
            'text': "Ask me about any movie, for example:",
            'fields': [("📖 Plot", "*Tell me about Inception*"),
                       ("🎬 Director", "*Who directed Titanic?*"),
                       ("📅 Release", "*When was Interstellar released?*"),
                       ("🎭 Cast", "*Who starred in The Matrix?*"),
                       ("⭐ Rating", "*Is Joker worth watching?*"),
                       ("🖼️ Poster", "*Show me the poster of Dune*"),
                       ("🎞️ Filmography", "*Which movies did Christopher Nolan direct?*"),
                       ("💡 Tip", "After a question, just ask *who directed it?*")]}
