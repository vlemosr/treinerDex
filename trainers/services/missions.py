from .experience import add_trainer_xp


MISSIONS = [
    {
        'key': 'outland-main',
        'title': 'Outland Main',
        'xp_reward': 22000000,
        'image': 'img/missions/outland-main.png',
    },
    {
        'key': 'league-kanto',
        'title': 'League Kanto',
        'xp_reward': 8000000,
        'image': 'img/missions/league-kanto.png',
    },
    {
        'key': 'outland-elders',
        'title': 'Outland Elders',
        'xp_reward': 12000000,
        'image': 'img/missions/outland-elders.png',
    },
    {
        'key': 'pks',
        'title': 'PKS',
        'xp_reward': 5200000,
        'image': 'img/missions/pks.png',
    },
    {
        'key': 'mewtwo',
        'title': 'Mewtwo',
        'xp_reward': 1250000,
        'image': 'img/missions/mewtwo.png',
    },
    {
        'key': 'johto-league',
        'title': 'Johto League',
        'xp_reward': 7000000,
        'image': 'img/missions/johto-league.png',
    },
    {
        'key': 'chosen',
        'title': 'Chosen',
        'xp_reward': 184500000,
        'image': 'img/missions/chosen.png',
    },
    {
        'key': 'secret-lab',
        'title': 'Secret Lab',
        'xp_reward': 12000000,
        'image': 'img/missions/secret-lab.png',
    },
    {
        'key': 'especializacao',
        'title': 'Especializacao',
        'xp_reward': 3000000,
        'image': 'img/missions/especializacao.png',
    },
    {
        'key': 'battle-factory',
        'title': 'Battle Factory',
        'xp_reward': 9000000,
        'image': 'img/missions/battle-factory.png',
    },
    {
        'key': 'celebi',
        'title': 'Celebi',
        'xp_reward': 950000,
        'image': 'img/missions/celebi.png',
    },
    {
        'key': 'time-traveler',
        'title': 'Time Traveler',
        'xp_reward': 51000000,
        'image': 'img/missions/time-traveler.png',
    },
]

MISSION_BY_KEY = {mission['key']: mission for mission in MISSIONS}


def format_xp(value):
    return f'{int(value):,}'.replace(',', '.')


def get_missions_for_trainer(trainer):
    completed_keys = set(
        trainer.mission_completions.values_list('mission_key', flat=True)
    )

    missions = []
    for mission in MISSIONS:
        mission_data = mission.copy()
        mission_data['completed'] = mission['key'] in completed_keys
        mission_data['formatted_xp'] = format_xp(mission['xp_reward'])
        missions.append(mission_data)
    return missions


def get_mission(mission_key):
    return MISSION_BY_KEY.get(mission_key)


def complete_mission_for_trainer(trainer, mission_key):
    from ..models import Mission, MissionCompletion

    mission = get_mission(mission_key)
    if mission is None:
        return None, False, None

    mission_obj, _ = Mission.objects.get_or_create(
        key=mission['key'],
        defaults={
            'title': mission['title'],
            'xp_reward': mission['xp_reward'],
        },
    )

    completion, created = MissionCompletion.objects.get_or_create(
        trainer=trainer,
        mission_key=mission['key'],
        defaults={'xp_reward': mission['xp_reward'], 'mission': mission_obj},
    )
    if completion.mission_id is None:
        completion.mission = mission_obj
        completion.save(update_fields=['mission'])

    progress = None
    if created:
        progress = add_trainer_xp(trainer, mission['xp_reward'])

    return completion, created, progress
