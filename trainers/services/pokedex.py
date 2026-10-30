import json
from functools import lru_cache
from pathlib import Path


POKEDEX_LIMIT = 649
DATA_FILE = Path(__file__).resolve().parent.parent / 'data' / 'pokemon_649.json'


def search_pokemon(query, registered_numbers=None, registered_only=False):
    registered_numbers = registered_numbers or set()
    normalized_query = query.strip().lower()
    if not normalized_query:
        results = _local_pokedex()
    else:
        results = [
            pokemon
            for pokemon in _local_pokedex()
            if _matches(pokemon, normalized_query)
        ]
        if not results:
            pokebase_result = _search_with_pokebase(normalized_query)
            if pokebase_result and pokebase_result['number'] <= POKEDEX_LIMIT:
                results = [pokebase_result]

    if registered_only:
        results = [
            pokemon
            for pokemon in results
            if pokemon['number'] in registered_numbers
        ]

    return [
        {
            **pokemon,
            'registered': pokemon['number'] in registered_numbers,
        }
        for pokemon in results
    ]


def pokemon_exists(number):
    return any(pokemon['number'] == number for pokemon in _local_pokedex())


def find_pokemon_by_number(number):
    number = int(number)
    return next(
        (pokemon for pokemon in _local_pokedex() if pokemon['number'] == number),
        None,
    )


def find_pokemon_by_name(name):
    normalized_name = name.strip().lower()
    if not normalized_name:
        return None

    for pokemon in _local_pokedex():
        if pokemon['name'].lower() == normalized_name:
            return pokemon

    matches = [
        pokemon
        for pokemon in _local_pokedex()
        if normalized_name in pokemon['name'].lower()
    ]
    return matches[0] if len(matches) == 1 else None


@lru_cache(maxsize=1)
def _local_pokedex():
    with DATA_FILE.open(encoding='utf-8') as pokemon_file:
        return json.load(pokemon_file)


def _matches(pokemon, query):
    values = [
        pokemon['name'].lower(),
        str(pokemon['number']),
        f"#{pokemon['number']:03d}",
        *[pokemon_type.lower() for pokemon_type in pokemon['types']],
    ]
    return any(query in value for value in values)


def _search_with_pokebase(query):
    try:
        import pokebase as pb
    except ImportError:
        return None

    try:
        pokemon = pb.pokemon(query)
    except Exception:
        return None

    if not getattr(pokemon, 'id_', None):
        return None

    types = [
        slot.type.name.title()
        for slot in getattr(pokemon, 'types', [])
        if getattr(slot, 'type', None)
    ]

    return {
        'number': pokemon.id_,
        'name': pokemon.name.title(),
        'types': types,
        'image': getattr(getattr(pokemon, 'sprites', None), 'front_default', ''),
    }
