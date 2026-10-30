from pokebase.common import SPRITE_URL


INVENTORY_SLOT_COUNT = 40
TEAM_SLOT_COUNT = 6

BASE_INVENTORY = [
    ('Poké Ball', 200, 'poke-ball'),
    ('Great Ball', 150, 'great-ball'),
    ('Ultra Ball', 100, 'ultra-ball'),
    ('Master Ball', 1, 'master-ball'),
    ('Potion', 200, 'potion'),
]

CLAN_STONES = {
    'orebound': [('Rock Stone', 5, 'hard-stone'), ('Earth Stone', 5, 'soft-sand')],
    'psycraft': [('Enigma Stone', 10, 'twisted-spoon')],
    'raibolt': [('Thunder Stone', 10, 'thunder-stone')],
    'seavel': [('Water Stone', 10, 'water-stone')],
    'volcanic': [('Fire Stone', 10, 'fire-stone')],
    'ironheart': [('Metal Stone', 5, 'metal-coat')],
    'malefic': [('Venom Stone', 10, 'poison-barb')],
    'naturia': [('Leaf Stone', 10, 'leaf-stone')],
    'gardestrike': [('Punch Stone', 10, 'black-belt')],
    'windgeon': [('Feather Stone', 10, 'sharp-beak')],
}


def get_pokebase_item_image(item_slug):
    return f'{SPRITE_URL}/items/{item_slug}.png'


def initialize_trainer_inventory(trainer):
    if trainer.inventory_initialized:
        return

    initial_items = [*BASE_INVENTORY, *CLAN_STONES.get(trainer.clan, [])]
    from ..models import InventoryItem

    InventoryItem.objects.bulk_create([
        InventoryItem(
            trainer=trainer,
            slot_number=slot_number,
            name=name,
            quantity=quantity,
            image_path=get_pokebase_item_image(item_slug),
        )
        for slot_number, (name, quantity, item_slug) in enumerate(initial_items, start=1)
    ])
    trainer.inventory_initialized = True
    trainer.save(update_fields=['inventory_initialized', 'updated_at'])


def get_inventory_slots(trainer):
    items_by_slot = {
        item.slot_number: item
        for item in trainer.inventory_items.all()
    }

    return [
        {
            'number': slot_number,
            'item': items_by_slot.get(slot_number),
        }
        for slot_number in range(1, INVENTORY_SLOT_COUNT + 1)
    ]


def get_team_slots(trainer):
    from .pokedex import find_pokemon_by_number

    members_by_slot = {
        member.slot_number: member
        for member in trainer.team_members.all()
    }
    slots = []
    for slot_number in range(1, TEAM_SLOT_COUNT + 1):
        member = members_by_slot.get(slot_number)
        slots.append({
            'number': slot_number,
            'member': member,
            'pokemon': find_pokemon_by_number(member.pokemon_number) if member else None,
        })
    return slots


def get_pokemon_deposit(trainer):
    from .pokedex import find_pokemon_by_number

    team_numbers = set(trainer.team_members.values_list('pokemon_number', flat=True))
    registered_numbers = trainer.pokedex_registrations.exclude(
        pokemon_number__in=team_numbers
    ).values_list('pokemon_number', flat=True)
    return [
        pokemon
        for number in registered_numbers
        if (pokemon := find_pokemon_by_number(number)) is not None
    ]
