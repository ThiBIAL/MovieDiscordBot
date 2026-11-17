"""Bot météo du TP1, extrait du notebook pour être réutilisé par le bot Discord."""
import os
import random
import re
from datetime import datetime, timedelta

import nltk
import requests
from dotenv import load_dotenv

nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)
from nltk.corpus import wordnet  

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/"


keywords = {
    'weather':   ['weather', 'rain', 'temperature', 'sunrise', 'cold',
                  'hot', 'sunny', 'cloudy', 'snow', 'wind', 'forecast'],
    'greetings': ['hello', 'hi', 'hey', 'howdy', 'hullo', 'how do you do'],
    'goodbye':   ['bye', 'goodbye', 'farewell', 'see you', 'quit', 'exit'],
    'thanks':    ['thanks', 'thank you', 'grateful'],
    'name':      ['name', 'called', 'who are you'],
    'age':       ['age', 'old', 'born'],
    'gender':    ['gender', 'boy', 'girl', 'male', 'female'],
    'time':      ['time', 'hour', 'clock'],
    'feeling':   ['how are you', 'fine', 'good', 'sad', 'happy'],
}

responses = {
    'weather':   ["Which city do you want the weather for?",
                  "Sure! Tell me the city, e.g. 'what is the weather like in Paris?'"],
    'greetings': ['Hello! How can I help you today?', 'Hi, you look well today!',
                  'Welcome here!', 'Hiii... I am a Bot, how are you?'],
    'goodbye':   ['Goodbye, have a nice day!', 'See you soon!', 'Bye, take care!'],
    'thanks':    ["You're welcome!", 'Anytime!', 'My pleasure :)'],
    'name':      ["I'm WeatherBot, nice to meet you!", 'You can call me Bot.'],
    'age':       ["I'm a computer program, I don't really have an age!",
                  'I was born when you ran this bot :)'],
    'gender':    ["I'm a bot, I don't have a gender.", 'Neither, I am made of code!'],
    'time':      ['TIME'],
    'feeling':   ["I'm doing great, thanks for asking!", 'All good on my side, and you?'],
    'default':   ["Sorry, I didn't understand.", 'Can you rephrase that?',
                  "I'm not sure I got that, try another question."],
}

def extend_keywords(keywords, max_synsets=3):
    extended = {}
    for intent, words in keywords.items():
        synonyms = set(words)
        for word in words:
            for syn in wordnet.synsets(word)[:max_synsets]:
                for lemma in syn.lemmas():
                    name = lemma.name().replace('_', ' ').lower()
                    if re.fullmatch(r"[a-z ]+", name):
                        synonyms.add(name)
        extended[intent] = sorted(synonyms)
    return extended


def word_to_regex(word):
    word = re.sub(r"(.)\1+", r"\1", word)
    parts = []
    for c in word:
        if c == ' ':
            parts.append(r"\s+")
        elif c in "aeiou" and len(word) >= 4:
            parts.append("[aeiou]+")
        else:
            parts.append(c + "+")
    return "".join(parts)


keywords_ext = extend_keywords(keywords)
patterns = {
    intent: '|'.join(r".*\b" + word_to_regex(w) + r"\b.*" for w in words)
    for intent, words in keywords_ext.items()
}


def matchPattern(user_msg):
    user_msg = user_msg.lower()
    for intent, pattern in patterns.items():
        if re.search(pattern, user_msg):
            return intent
    return None


def getResponse(intent):
    if intent is None:
        intent = 'default'
    return random.choice(responses[intent])

CITY = r"(?P<city>[a-z]+(?:[\s-][a-z]+)*?)"
TIME = r"(?:\s+(?P<time>today|tomorrow|the day after tomorrow|tonight|now))?"
END = r"\s*[?.!]?$"
COND = r"(?P<condition>cold|hot|warm|rainy|raining|rain|sunny|cloudy|windy|snowy|snowing|snow)"

weather_patterns = [
    r"what(?:\s+is|'s)\s+the\s+weather\s+(?:like\s+)?in\s+" + CITY + TIME + END,
    r"how\s+is\s+the\s+weather\s+in\s+" + CITY + TIME + END,
    r"(?:is|will)\s+it\s+(?:be\s+)?" + COND + r"\s+in\s+" + CITY + TIME + END,
    r".*\bweather\b.*?\bin\s+" + CITY + TIME + END,
]


def createEntities(user_msg):
    user_msg = user_msg.lower().strip()
    entities = {'city': None, 'time': None, 'condition': None}

    for p in weather_patterns:
        m = re.match(p, user_msg)
        if m:
            for key, value in m.groupdict().items():
                if value:
                    entities[key] = value
            return {'intent': 'get weather', 'entities': entities}

    if matchPattern(user_msg) == 'weather':
        return {'intent': 'get weather', 'entities': entities}
    return None

DAY_OFFSET = {'today': 0, 'now': 0, 'tonight': 0,
              'tomorrow': 1, 'the day after tomorrow': 2}


def getWeather(location, date='today'):
    offset = DAY_OFFSET.get(date, 0)
    endpoint = 'weather' if offset == 0 else 'forecast'
    params = {'q': location, 'appid': API_KEY, 'units': 'metric'}

    try:
        r = requests.get(BASE_URL + endpoint, params=params, timeout=10)
    except requests.RequestException:
        return {'error': "I can't reach the weather service right now."}

    if r.status_code == 401:
        return {'error': "Invalid API key (401). Check your key or wait for its activation."}
    if r.status_code == 404:
        return {'error': f"I couldn't find the city '{location.title()}' (404)."}
    if r.status_code == 400:
        return {'error': "Bad request (400)."}
    if r.status_code != 200:
        return {'error': f"Weather service error ({r.status_code})."}

    data = r.json()

    if offset == 0:
        return {'city': data['name'], 'country': data['sys']['country'],
                'temp': data['main']['temp'],
                'main': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
                'wind': data['wind']['speed']}

    target = (datetime.now() + timedelta(days=offset)).strftime('%Y-%m-%d')
    candidates = [x for x in data['list'] if x['dt_txt'].startswith(target)]
    if not candidates:
        return {'error': "No forecast available for that day."}
    item = min(candidates, key=lambda x: abs(int(x['dt_txt'][11:13]) - 12))
    return {'city': data['city']['name'], 'country': data['city']['country'],
            'temp': item['main']['temp'],
            'main': item['weather'][0]['main'],
            'description': item['weather'][0]['description'],
            'wind': item['wind']['speed']}

def bold(text):
    return f"**{text}**"


def describeTemp(t):
    if t < 0:  return 'freezing', '🥶'
    if t < 10: return 'very cold', '🥶'
    if t < 16: return 'cool', '🧥'
    if t < 22: return 'mild', '🙂'
    if t < 28: return 'warm', '😎'
    return 'very hot', '🥵'


WEATHER_EMOJI = {'Clear': '☀️', 'Clouds': '☁️', 'Rain': '🌧️', 'Drizzle': '🌦️',
                 'Thunderstorm': '⛈️', 'Snow': '❄️', 'Mist': '🌫️', 'Fog': '🌫️', 'Haze': '🌫️'}


GIPHY = "https://media.giphy.com/media/{}/giphy.gif"
WEATHER_GIF = {
    'Clear':        GIPHY.format("PWE9TqGFHlbctObBjN"),
    'Clouds':       GIPHY.format("gk3s6G7AdUNkey0YpE"),
    'Rain':         GIPHY.format("GwaFHlGnMSF0uQnmuq"),
    'Drizzle':      GIPHY.format("sUmfD5CnsTFyvnYGcd"),
    'Thunderstorm': GIPHY.format("mTdVKHLEFTGWQ"),
    'Snow':         GIPHY.format("HdbuxhHANUxttTsgZv"),
    'Mist':         GIPHY.format("l4pT0NtPSMV3pw6Lm"),
    'Fog':          GIPHY.format("l4pT0NtPSMV3pw6Lm"),
    'Haze':         GIPHY.format("l4pT0NtPSMV3pw6Lm"),
}
DEFAULT_GIF = GIPHY.format("za5xikuRr0OzK")


def getGif(w):
    return WEATHER_GIF.get(w['main'], DEFAULT_GIF)


def humanReply(w, time):
    word, temp_emoji = describeTemp(w['temp'])
    verb = "It is" if time in ('today', 'now', 'tonight') else "It will be"
    when = "" if time in ('today', 'now') else f" {time}"
    place = bold(f"{w['city']}, {w['country']}")
    temp_str = bold(f"{w['temp']:.0f}°C")
    sky = WEATHER_EMOJI.get(w['main'], '🌍')
    return f"{verb} {word} in {place}{when}, with {temp_str} {temp_emoji}. Sky: {w['description']} {sky}"


NORMALIZE = {'rain': 'rainy', 'raining': 'rainy', 'snow': 'snowy', 'snowing': 'snowy'}

CONDITION_CHECK = {
    'cold':   lambda w: w['temp'] < 10,
    'hot':    lambda w: w['temp'] > 25,
    'warm':   lambda w: w['temp'] > 18,
    'rainy':  lambda w: w['main'] in ('Rain', 'Drizzle', 'Thunderstorm'),
    'sunny':  lambda w: w['main'] == 'Clear',
    'cloudy': lambda w: w['main'] == 'Clouds',
    'snowy':  lambda w: w['main'] == 'Snow',
    'windy':  lambda w: w.get('wind', 0) > 8,
}


def answerCondition(w, cond, time):
    cond = NORMALIZE.get(cond, cond)
    answer = "✅ Yes" if CONDITION_CHECK[cond](w) else "❌ No"
    return f"{answer}! " + humanReply(w, time)


def reply(user_msg):
    """Renvoie {'text': str, 'weather': dict | None}.
    'weather' n'est rempli que pour une vraie réponse météo (sinon None)."""
    user_msg = user_msg.strip()
    if not user_msg:
        return {'text': getResponse('default'), 'weather': None}

    result = createEntities(user_msg)
    if result:
        ents = result['entities']
        if not ents['city']:
            return {'text': "For which city? 🌍 (e.g. *what is the weather like in Paris tomorrow?*)",
                    'weather': None}
        time = ents['time'] or 'today'

        weather = getWeather(ents['city'], time)
        if 'error' in weather:
            return {'text': "⚠️ " + weather['error'], 'weather': None}
        if ents['condition']:
            text = answerCondition(weather, ents['condition'], time)
        else:
            text = humanReply(weather, time)
        return {'text': text, 'weather': weather}

    intent = matchPattern(user_msg)
    if intent == 'time':
        return {'text': "It is " + datetime.now().strftime("%H:%M") + " 🕒", 'weather': None}
    return {'text': getResponse(intent), 'weather': None}
