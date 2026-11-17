"""Génère data/nlu.yml : >= 100 exemples variés par intent, entités annotées,
lookup table de films et synonymes.

Usage : python generate_nlu.py   (puis : rasa train nlu)
"""
import random
from pathlib import Path

random.seed(42)
N_PER_INTENT = 120

MOVIES = [
    "Iron Man", "Inception", "Interstellar", "The Dark Knight", "Titanic", "Avatar",
    "The Matrix", "Gladiator", "Jurassic Park", "The Godfather", "Pulp Fiction",
    "Forrest Gump", "Fight Club", "The Lord of the Rings", "Spider Man", "Toy Story",
    "Finding Nemo", "The Lion King", "Frozen", "Shrek", "Up", "Coco", "Joker",
    "Parasite", "Oppenheimer", "Barbie", "Dune", "Avengers Endgame", "Black Panther",
    "Star Wars", "Back to the Future", "The Shawshank Redemption", "Schindler's List",
    "The Untouchables", "Amelie", "La La Land", "Whiplash", "Gravity", "Alien",
    "Terminator", "Rocky", "Jaws", "E.T.", "Psycho", "Casablanca", "Goodfellas",
    "The Silence of the Lambs", "Saving Private Ryan", "The Prestige", "Memento",
    "Tenet", "Dunkirk", "Django Unchained", "Inglourious Basterds", "Kill Bill",
    "The Social Network", "Gone Girl", "Se7en", "The Revenant", "Mad Max Fury Road",
    "Blade Runner", "Ratatouille", "Wall-E", "Inside Out", "Spirited Away",
    "Harry Potter", "The Hunger Games", "Pirates of the Caribbean", "Top Gun",
    "Mission Impossible", "The Truman Show", "The Grand Budapest Hotel", "Her",
    "Get Out", "Everything Everywhere All at Once", "No Country for Old Men",
    "The Green Mile", "Braveheart", "The Departed", "Heat", "Shutter Island",
    "Catch Me If You Can", "The Wolf of Wall Street", "Moana", "Encanto",
]

TRAIN_MOVIES = MOVIES[:70]

PEOPLE = [
    "Christopher Nolan", "Steven Spielberg", "Quentin Tarantino", "Martin Scorsese",
    "James Cameron", "Ridley Scott", "Denis Villeneuve", "Greta Gerwig", "Bong Joon-ho",
    "David Fincher", "Wes Anderson", "Hayao Miyazaki", "Peter Jackson", "Tim Burton",
    "Leonardo DiCaprio", "Tom Hanks", "Brad Pitt", "Robert Downey Jr", "Scarlett Johansson",
    "Meryl Streep", "Morgan Freeman", "Natalie Portman", "Keanu Reeves", "Tom Cruise",
    "Margot Robbie", "Ryan Gosling", "Emma Stone", "Denzel Washington", "Cillian Murphy",
    "Matt Damon", "Johnny Depp", "Zendaya", "Timothee Chalamet", "Anne Hathaway",
    "Christian Bale", "Joaquin Phoenix", "Harrison Ford", "Al Pacino", "Robert De Niro",
    "Jennifer Lawrence",
]


MOVIE_TEMPLATES = {
    "movieinfo": [
        "tell me about {m}", "what is {m} about", "give me info on {m}", "info about {m}",
        "what's the plot of {m}", "summary of {m}", "can you describe {m}",
        "i want to know more about {m}", "what happens in {m}", "do you know the movie {m}",
        "{m} plot", "what is the story of {m}", "give me a summary of {m}",
        "tell me something about the film {m}", "what's {m} about", "can you tell me about {m}",
        "overview of {m}", "describe the movie {m} to me", "i'd like information about {m}",
        "have you heard of {m}", "explain the plot of {m}", "synopsis of {m}",
        "what kind of movie is {m}", "give me details about {m}", "what do you know about {m}",
        "tell me more about the movie {m}", "{m} summary", "info on the film {m}",
    ],
    "director": [
        "who directed {m}", "who is the director of {m}", "who made {m}", "director of {m}",
        "who was behind the camera for {m}", "{m} was directed by who",
        "tell me the director of {m}", "who's the director of {m}", "which director made {m}",
        "do you know who directed {m}", "name the director of {m}", "who filmed {m}",
        "{m} director", "i want to know who directed {m}", "who helmed {m}",
        "who was the filmmaker of {m}", "can you tell me who directed {m}",
        "by whom was {m} directed", "who directed the movie {m}", "who is behind {m}",
        "who was the director of the film {m}", "which filmmaker directed {m}",
    ],
    "releaseYear": [
        "when was {m} released", "what year did {m} come out", "release date of {m}",
        "when did {m} come out", "{m} release year", "in which year was {m} released",
        "when was {m} out in theaters", "what is the release date of {m}",
        "how old is the movie {m}", "when did {m} hit the cinemas", "what year is {m} from",
        "release year of {m}", "when was the film {m} released", "do you know when {m} came out",
        "tell me when {m} was released", "{m} came out when", "when did they release {m}",
        "which year did {m} premiere", "when was {m} first shown", "when did {m} premiere",
        "{m} release date", "what year was {m} made",
    ],
    "actors": [
        "who played in {m}", "who are the actors of {m}", "who starred in {m}",
        "main actor of {m}", "cast of {m}", "who is in {m}", "who was the main actor in {m}",
        "list the actors of {m}", "who plays the lead in {m}", "tell me the cast of {m}",
        "which actors are in {m}", "{m} cast", "who acted in {m}",
        "who are the main actors of {m}", "who was the star of {m}", "give me the cast of {m}",
        "who's in the movie {m}", "show me the actors of {m}", "who stars in {m}",
        "what actors played in {m}", "who was the main actress in {m}", "{m} actors",
    ],
    "poster": [
        "show me the poster of {m}", "{m} poster", "can i see the poster for {m}",
        "send me the poster of {m}", "what does the poster of {m} look like",
        "give me the {m} poster", "display the poster of {m}", "i want to see the poster of {m}",
        "poster for {m}", "show me the cover of {m}", "send the movie poster of {m}",
        "picture of {m}", "image of the movie {m}", "show me an image of {m}",
        "get me the poster of {m}", "let me see the {m} poster",
        "i'd like to see the poster of {m}", "the poster of {m} please", "show {m} poster",
        "can you send a picture of {m}", "affiche of {m}", "show me what {m} looks like",
    ],
    "rating": [
        "what is the rating of {m}", "is {m} good", "how good is {m}",
        "what's the score of {m}", "how is {m} rated", "{m} rating", "is {m} worth watching",
        "rating of {m}", "what do people think of {m}", "how well rated is {m}",
        "what's {m} rated", "is {m} a good movie", "should i watch {m}",
        "what score did {m} get", "how many stars does {m} have", "is {m} any good",
        "review score of {m}", "is the movie {m} good", "what grade does {m} have",
        "average rating for {m}", "{m} score", "do people like {m}",
    ],
}

PERSON_TEMPLATES = {
    "filmography": [
        "which movies did {p} direct", "what films has {p} made", "movies with {p}",
        "what movies did {p} play in", "give me films by {p}", "list the movies of {p}",
        "what are the best movies of {p}", "filmography of {p}", "show me movies starring {p}",
        "which films is {p} known for", "tell me movies with {p}", "what did {p} play in",
        "{p} movies", "recommend me a movie with {p}", "i like {p}, what should i watch",
        "famous movies of {p}", "what has {p} directed", "in which movies did {p} act",
        "movies directed by {p}", "{p} filmography", "what are {p}'s films",
        "give me a movie by {p}", "best films with {p}",
    ],
}


def combos(heads, tails):
    return [h + t for h in heads for t in tails]


BASIC = {
    "greet": combos(
        ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "yo", "hiya",
         "greetings", "howdy", "hey there", "hello there", "heya", "morning", "hi hi",
         "salut", "bonjour", "hey hey"],
        ["", " bot", " moviebot", "!", " friend", ", how are you", ", how's it going",
         " everyone", " buddy"]),
    "goodbye": combos(
        ["bye", "goodbye", "see you", "see you later", "farewell", "bye bye", "good night",
         "catch you later", "i'm leaving", "i have to go", "talk to you later", "ciao",
         "later", "take care", "see ya", "au revoir"],
        ["", " bot", "!", " moviebot", ", thanks", " friend", " for now", " :)"]),
    "thanks": combos(
        ["thanks", "thank you", "thx", "thanks a lot", "thank you so much", "much appreciated",
         "great thanks", "cool thanks", "perfect thank you", "awesome thanks", "merci",
         "thanks for the help", "that's helpful", "many thanks", "cheers", "ty"],
        ["", " bot", "!", " moviebot", " :)", " buddy", ", that's perfect", " a lot"]),
    "help": combos(
        ["help", "what can you do", "how do you work", "what are you able to do",
         "how can you help me", "what questions can i ask", "show me what you can do",
         "i need help", "what do you know", "give me some examples", "how does this work",
         "what are your features", "what kind of questions do you answer",
         "can you help me", "what should i ask you"],
        ["", "?", " please", " bot", " moviebot", ", i'm lost", " exactly", "!"]),
}

OUT_OF_SCOPE = (
    # messages très courts / vides de sens : sans eux, le modèle les classe avec trop de confiance
    ["movie", "film", "cat", "ok", "hmm", "test", "lol", "yes", "no", "what", "why", "iron",
     "blue", "car", "asdf", "?", "...", "random", "nothing", "idk"]
    + [f"what's the weather in {c}" for c in ["paris", "london", "tokyo", "berlin", "rome"]]
    + [f"is it going to rain in {c} tomorrow" for c in ["paris", "madrid", "oslo", "lyon"]]
    + [f"how do i cook {f}" for f in ["pasta", "rice", "a steak", "pancakes", "an omelette"]]
    + [f"give me a recipe for {f}" for f in ["pizza", "lasagna", "a cake", "cookies", "soup"]]
    + [f"what is {a} plus {b}" for a, b in [(2, 2), (5, 7), (10, 3), (12, 8), (100, 1)]]
    + [f"how much is {a} times {b}" for a, b in [(3, 4), (6, 7), (9, 9), (11, 2)]]
    + [f"book a flight to {c}" for c in ["new york", "rome", "dubai", "lisbon", "sydney"]]
    + [f"find me a hotel in {c}" for c in ["paris", "nice", "barcelona", "prague"]]
    + [f"what time is it in {c}" for c in ["tokyo", "new york", "london", "sydney"]]
    + [f"who won the {s} match yesterday" for s in ["football", "tennis", "rugby", "basketball"]]
    + [f"what's the price of {x}" for x in ["bitcoin", "gold", "an iphone", "a tesla"]]
    + [f"translate {w} into spanish" for w in ["hello", "cat", "thank you", "house"]]
    + [f"set an alarm for {h}" for h in ["7am", "6:30", "noon", "8 o'clock"]]
    + [f"play some {g} music" for g in ["rock", "jazz", "rap", "classical"]]
    + [
        "tell me a joke", "what is the capital of france", "how tall is the eiffel tower",
        "what's your favorite color", "do you like pizza", "can you do my homework",
        "write me a poem", "how do i fix my car", "what is python", "explain quantum physics",
        "order me a pizza", "call my mom", "what's the meaning of life", "i'm hungry",
        "how old is the earth", "what is love", "send an email to my boss",
        "how do i lose weight", "who is the president of the usa", "what's 2 to the power 10",
        "where is the nearest pharmacy", "turn off the lights", "how many legs does a spider have",
        "can you drive", "what's the best phone", "recommend me a restaurant",
        "how do i learn french", "what's the score of the game", "i need a taxi",
        "how do i reset my password", "what is machine learning", "buy me shoes",
        "what's the news today", "how far is the moon", "is coffee bad for you",
        "who invented the internet", "how do i make money", "what day is it today",
        "where do penguins live", "how do airplanes fly",
    ]
)

SYNONYMS = {
    "spider man": ["spiderman", "spider-man"],
    "the lord of the rings": ["lotr", "lord of the rings"],
    "star wars": ["starwars"],
    "avengers endgame": ["endgame", "avengers: endgame"],
    "the dark knight": ["dark knight"],
}


def vary_case(name):
    """Les utilisateurs n'écrivent pas toujours les majuscules."""
    return random.choice([name, name.lower(), name.lower()])


def finish(sentence):
    """Majuscule initiale et ponctuation aléatoires."""
    if random.random() < 0.3:
        sentence = sentence[0].upper() + sentence[1:]
    return sentence + random.choice(["", "", "?", " ?", "!"]) if not sentence.endswith(("?", "!")) else sentence


def generate(templates, slot, values, entity, n):
    out, tries = set(), 0
    while len(out) < n and tries < n * 50:
        tries += 1
        t = random.choice(templates)
        v = vary_case(random.choice(values))
        out.add(finish(t.replace(slot, f"[{v}]({entity})")))
    return sorted(out)


def generate_basic(sentences, n):
    pool = list(dict.fromkeys(sentences))
    random.shuffle(pool)
    return sorted(pool[:n])


def synonym_examples():
    """Quelques exemples annotés avec un synonyme -> valeur normalisée."""
    lines = []
    templates = ["tell me about {m}", "who directed {m}", "when was {m} released",
                 "who played in {m}", "show me the poster of {m}", "is {m} good"]
    for value, syns in SYNONYMS.items():
        for s in syns:
            t = random.choice(templates)
            lines.append((t, t.replace("{m}", f'[{s}]{{"entity": "movie", "value": "{value}"}}')))
    return lines


def block(intent, examples):
    body = "\n".join(f"    - {e}" for e in examples)
    return f"- intent: {intent}\n  examples: |\n{body}\n"


def main():
    parts = ['version: "3.1"\n\nnlu:\n']

    syn_by_intent = {}
    intent_of_template = {
        "tell me about {m}": "movieinfo", "who directed {m}": "director",
        "when was {m} released": "releaseYear", "who played in {m}": "actors",
        "show me the poster of {m}": "poster", "is {m} good": "rating",
    }
    for t, line in synonym_examples():
        syn_by_intent.setdefault(intent_of_template[t], []).append(line)

    for intent, templates in MOVIE_TEMPLATES.items():
        ex = generate(templates, "{m}", TRAIN_MOVIES, "movie", N_PER_INTENT)
        parts.append(block(intent, ex + syn_by_intent.get(intent, [])))
    for intent, templates in PERSON_TEMPLATES.items():
        parts.append(block(intent, generate(templates, "{p}", PEOPLE, "person", N_PER_INTENT)))
    for intent, sentences in BASIC.items():
        parts.append(block(intent, generate_basic(sentences, N_PER_INTENT)))
    parts.append(block("out_of_scope", sorted(set(OUT_OF_SCOPE))))

    for value, syns in SYNONYMS.items():
        parts.append(block_syn(value, syns))
    parts.append(lookup("movie", MOVIES))
    parts.append(lookup("person", PEOPLE))

    Path("data").mkdir(exist_ok=True)
    Path("data/nlu.yml").write_text("\n".join(parts), encoding="utf-8")
    print("data/nlu.yml written")


def block_syn(value, syns):
    body = "\n".join(f"    - {s}" for s in syns)
    return f"- synonym: {value}\n  examples: |\n{body}\n"


def lookup(name, values):
    body = "\n".join(f"    - {v.lower()}" for v in values)
    return f"- lookup: {name}\n  examples: |\n{body}\n"


if __name__ == "__main__":
    main()
