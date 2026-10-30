from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('trainers', '0013_remove_friend_region'),
    ]

    operations = [
        migrations.RenameField(
            model_name='friend',
            old_name='trainer_code',
            new_name='nickname',
        ),
        migrations.AlterField(
            model_name='friend',
            name='nickname',
            field=models.CharField(blank=True, max_length=40, verbose_name='apelido'),
        ),
    ]
