import asyncio, glob, os

from rasa.core.agent import Agent

HERE = os.path.dirname(os.path.abspath(__file__))
latest_model = max(glob.glob(os.path.join(HERE, "models", "*.tar.gz")), key=os.path.getmtime)
print("Loading", latest_model)
agent = Agent.load(latest_model)


INTENT_THRESHOLD = 0.5   # en dessous : on ne devine pas, on demande de reformuler
ENTITY_THRESHOLD = 0.5   # en dessous : l'entité est ignorée


def interpret(result):
    """Résultat brut de Rasa -> (intent, confiance, {entité: valeur})."""
    intent = result['intent']['name']
    confidence = result['intent']['confidence']
    if confidence < INTENT_THRESHOLD:
        intent = 'unclear'

    entities = {e['entity']: e['value'] for e in result['entities']
                if e.get('confidence_entity', 1.0) >= ENTITY_THRESHOLD}
    return intent, confidence, entities


def parse(text):
    """Version synchrone (scripts, tests). NE PAS utiliser dans le bot Discord :
    asyncio.run() plante si une boucle asyncio tourne déjà."""
    return interpret(asyncio.run(agent.parse_message(text)))


async def parse_async(text):
    """Version pour le bot Discord : on est déjà dans la boucle asyncio, on fait juste await."""
    return interpret(await agent.parse_message(text))


if __name__ == "__main__":
    for sentence in ["who directed inception", "hello", "tell me about spiderman",
                     "which movies did christopher nolan direct",
                     "who was the director of oppenheimer", "when did barbie come out",
                     "whats the weather like", "movie", "iron", "asdfgh qwerty"]:
        intent, confidence, entities = parse(sentence)
        print(f"{sentence!r:45} -> {intent:12} ({confidence:.2f})  {entities}")
