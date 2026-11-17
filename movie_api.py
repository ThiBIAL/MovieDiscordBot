"""Accès à l'API TheMovieDB (TMDB) : recherche de films / personnes et détails."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3/"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"
MOVIE_PAGE = "https://www.themoviedb.org/movie/{}"
PERSON_PAGE = "https://www.themoviedb.org/person/{}"


class TMDBError(Exception):
    """Erreur lisible par l'utilisateur (réseau, clé invalide...)."""


def _get(endpoint, **params):
    params['api_key'] = API_KEY
    try:
        r = requests.get(BASE_URL + endpoint, params=params, timeout=10)
    except requests.RequestException:
        raise TMDBError("I can't reach TheMovieDB right now, try again in a moment.")
    if r.status_code == 401:
        raise TMDBError("My TMDB API key is invalid (401).")
    if r.status_code != 200:
        raise TMDBError(f"TheMovieDB returned an error ({r.status_code}).")
    return r.json()


def image(path):
    return IMAGE_URL + path if path else None


def search_movie(title):
    """Renvoie l'id du film le plus pertinent, ou None s'il n'existe pas."""
    results = _get("search/movie", query=title)['results']
    if not results:
        return None
    def score(m):
        bonus = 3 if _norm(m['title']) == _norm(title) else 1
        return m.get('vote_count', 0) * bonus

    return max(results[:5], key=score)['id']


def _norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def get_movie(movie_id):
    """Détails + équipe/casting en un seul appel (append_to_response)."""
    d = _get(f"movie/{movie_id}", append_to_response="credits")
    crew, cast = d['credits']['crew'], d['credits']['cast']
    return {
        'id': d['id'],
        'title': d['title'],
        'tagline': d.get('tagline') or "",
        'overview': d.get('overview') or "No summary available.",
        'release_date': d.get('release_date') or "",
        'year': (d.get('release_date') or "????")[:4],
        'rating': d.get('vote_average', 0),
        'votes': d.get('vote_count', 0),
        'runtime': d.get('runtime') or 0,
        'genres': [g['name'] for g in d.get('genres', [])],
        'poster': image(d.get('poster_path')),
        'directors': [p['name'] for p in crew if p['job'] == 'Director'],
        'cast': [(p['name'], p.get('character') or "") for p in cast[:5]],
        'url': MOVIE_PAGE.format(d['id']),
    }


def search_person(name):
    results = _get("search/person", query=name)['results']
    if not results:
        return None
    p = results[0]
    return {'id': p['id'], 'name': p['name'],
            'department': p.get('known_for_department', 'Acting'),
            'photo': image(p.get('profile_path')),
            'url': PERSON_PAGE.format(p['id'])}


def get_filmography(person, limit=8):
    """Films les plus connus : réalisés si c'est un réalisateur, joués sinon."""
    credits = _get(f"person/{person['id']}/movie_credits")
    if person['department'] == 'Directing':
        movies = [m for m in credits['crew'] if m.get('job') == 'Director']
    else:
        movies = credits['cast']

    seen, unique = set(), []
    for m in sorted(movies, key=lambda m: m.get('vote_count', 0), reverse=True):
        if m['id'] not in seen and m.get('release_date'):
            seen.add(m['id'])
            unique.append((m['title'], m['release_date'][:4]))
    return unique[:limit]
