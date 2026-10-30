import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('trainers', '0009_inventoryitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainerTeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_number', models.PositiveSmallIntegerField()),
                ('pokemon_number', models.PositiveIntegerField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_members', to='trainers.trainerprofile')),
            ],
            options={
                'verbose_name': 'membro da equipe',
                'verbose_name_plural': 'membros da equipe',
                'ordering': ['slot_number'],
                'constraints': [
                    models.UniqueConstraint(fields=('trainer', 'slot_number'), name='unique_team_slot_per_trainer'),
                    models.UniqueConstraint(fields=('trainer', 'pokemon_number'), name='unique_pokemon_per_trainer_team'),
                    models.CheckConstraint(condition=models.Q(('slot_number__gte', 1), ('slot_number__lte', 6)), name='team_slot_between_1_and_6'),
                ],
            },
        ),
    ]
