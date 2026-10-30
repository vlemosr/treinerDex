from django.conf import settings
from django.db import models
from django.templatetags.static import static


class TrainerProfile(models.Model):
    CITY_CHOICES = [
        ('pallet_town', 'Pallet Town'),
        ('viridian_city', 'Viridian City'),
        ('pewter_city', 'Pewter City'),
        ('cerulean_city', 'Cerulean City'),
        ('vermilion_city', 'Vermilion City'),
        ('lavender_town', 'Lavender Town'),
        ('celadon_city', 'Celadon City'),
        ('fuchsia_city', 'Fuchsia City'),
        ('saffron_city', 'Saffron City'),
        ('cinnabar_island', 'Cinnabar Island'),
    ]

    GENDER_CHOICES = [
        ('female', 'Feminino'),
        ('male', 'Masculino'),
    ]

    CLAN_CHOICES = [
        ('orebound', 'Orebound'),
        ('seavel', 'Seavel'),
        ('naturia', 'Naturia'),
        ('windgeon', 'Windgeon'),
        ('psycraft', 'Psycraft'),
        ('malefic', 'Malefic'),
        ('volcanic', 'Volcanic'),
        ('ironheart', 'Ironheart'),
        ('raibolt', 'Raibolt'),
        ('gardestrike', 'GardeStrike'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trainer_profiles',
    )
    trainer_name = models.CharField('nome do treinador', max_length=80)
    gender = models.CharField('genero', max_length=24, choices=GENDER_CHOICES)
    city = models.CharField('cidade', max_length=40, choices=CITY_CHOICES)
    clan = models.CharField('cla', max_length=24, choices=CLAN_CHOICES)
    level = models.PositiveIntegerField(default=1)
    current_xp = models.PositiveIntegerField(default=0)
    next_level_xp = models.PositiveIntegerField(default=98)
    current_hp = models.PositiveIntegerField(default=100)
    max_hp = models.PositiveIntegerField(default=100)
    avatar = models.ImageField(upload_to='trainer_avatars/', blank=True, null=True)
    inventory_initialized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'perfil de treinador'
        verbose_name_plural = 'perfis de treinadores'

    def __str__(self):
        return self.trainer_name


class PokedexRegistration(models.Model):
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='pokedex_registrations',
    )
    pokemon_number = models.PositiveIntegerField()
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['pokemon_number']
        constraints = [
            models.UniqueConstraint(
                fields=['trainer', 'pokemon_number'],
                name='unique_pokedex_registration_per_trainer',
            ),
        ]
        verbose_name = 'registro da Pokedex'
        verbose_name_plural = 'registros da Pokedex'

    def __str__(self):
        return f'{self.trainer} - #{self.pokemon_number:03d}'


class Friend(models.Model):
    STATUS_CHOICES = [
        ('added', 'Adicionado'),
        ('invited', 'Convite enviado'),
    ]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='friends',
    )
    name = models.CharField('nome do amigo', max_length=80)
    contact = models.CharField('contato', max_length=120, blank=True)
    nickname = models.CharField('apelido', max_length=40, blank=True)
    clan = models.CharField('cla', max_length=24, choices=TrainerProfile.CLAN_CHOICES, blank=True)
    city = models.CharField('cidade', max_length=40, choices=TrainerProfile.CITY_CHOICES, blank=True)
    level = models.PositiveIntegerField('nivel', default=1)
    notes = models.TextField('observacoes', blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='added')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['trainer', 'name'],
                name='unique_friend_name_per_trainer',
            ),
        ]
        verbose_name = 'amigo'
        verbose_name_plural = 'amigos'

    def __str__(self):
        return self.name


class MissionCompletion(models.Model):
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='mission_completions',
    )
    mission_key = models.CharField(max_length=80)
    xp_reward = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['trainer', 'mission_key'],
                name='unique_mission_completion_per_trainer',
            ),
        ]
        verbose_name = 'missao concluida'
        verbose_name_plural = 'missoes concluidas'

    def __str__(self):
        return f'{self.trainer} - {self.mission_key}'


class InventoryItem(models.Model):
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='inventory_items',
    )
    slot_number = models.PositiveSmallIntegerField()
    name = models.CharField('nome do item', max_length=80)
    quantity = models.PositiveIntegerField(default=1)
    image_path = models.CharField('imagem do item', max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['slot_number']
        constraints = [
            models.UniqueConstraint(
                fields=['trainer', 'slot_number'],
                name='unique_inventory_slot_per_trainer',
            ),
            models.CheckConstraint(
                condition=models.Q(slot_number__gte=1, slot_number__lte=40),
                name='inventory_slot_between_1_and_40',
            ),
        ]
        verbose_name = 'item do inventario'
        verbose_name_plural = 'itens do inventario'

    def __str__(self):
        return f'{self.trainer} - slot {self.slot_number}: {self.name}'

    @property
    def image_url(self):
        if self.image_path.startswith(('http://', 'https://', 'data:')):
            return self.image_path
        return static(self.image_path) if self.image_path else ''


class TrainerTeamMember(models.Model):
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='team_members',
    )
    slot_number = models.PositiveSmallIntegerField()
    pokemon_number = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['slot_number']
        constraints = [
            models.UniqueConstraint(
                fields=['trainer', 'slot_number'],
                name='unique_team_slot_per_trainer',
            ),
            models.UniqueConstraint(
                fields=['trainer', 'pokemon_number'],
                name='unique_pokemon_per_trainer_team',
            ),
            models.CheckConstraint(
                condition=models.Q(slot_number__gte=1, slot_number__lte=6),
                name='team_slot_between_1_and_6',
            ),
        ]
        verbose_name = 'membro da equipe'
        verbose_name_plural = 'membros da equipe'

    def __str__(self):
        return f'{self.trainer} - equipe {self.slot_number}: #{self.pokemon_number:03d}'
