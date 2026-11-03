from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Friend,
    InventoryItem,
    MissionCompletion,
    PokedexRegistration,
    TrainerProfile,
    TrainerTeamMember,
)
from .services.experience import (
    add_trainer_xp,
    get_level_for_total_xp,
    get_level_progress,
    get_max_hp_for_level,
    get_total_xp_for_level,
)


class ExperienceProgressionTests(TestCase):
    def test_hp_progression_matches_reference_level(self):
        self.assertEqual(get_max_hp_for_level(1), 100)
        self.assertEqual(get_max_hp_for_level(333), 5100)

    def test_level_table_uses_cumulative_xp_from_reference_images(self):
        self.assertEqual(get_total_xp_for_level(1), 0)
        self.assertEqual(get_total_xp_for_level(2), 98)
        self.assertEqual(get_total_xp_for_level(99), 15219367)
        self.assertEqual(get_total_xp_for_level(100), 15688100)
        self.assertEqual(get_total_xp_for_level(201), 131359933)
        self.assertEqual(get_total_xp_for_level(300), 441084700)

    def test_level_up_cost_is_difference_between_cumulative_levels(self):
        xp_to_level_100 = get_total_xp_for_level(100) - get_total_xp_for_level(99)

        self.assertEqual(xp_to_level_100, 468733)

    def test_progress_bar_uses_current_level_slice(self):
        level_99_xp = get_total_xp_for_level(99)
        level_100_xp = get_total_xp_for_level(100)
        halfway_total_xp = level_99_xp + ((level_100_xp - level_99_xp) // 2)

        progress = get_level_progress(halfway_total_xp)

        self.assertEqual(progress['level'], 99)
        self.assertEqual(progress['gained_this_level'], 234366)
        self.assertEqual(progress['needed_for_next_level'], 468733)
        self.assertAlmostEqual(progress['percent'], 50, delta=0.01)

    def test_total_xp_maps_to_level_and_updates_trainer(self):
        user = User.objects.create_user(username='xpuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='XpUser',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )

        progress = add_trainer_xp(trainer, get_total_xp_for_level(100))
        trainer.refresh_from_db()

        self.assertEqual(get_level_for_total_xp(trainer.current_xp), 100)
        self.assertEqual(progress['level'], 100)
        self.assertEqual(trainer.level, 100)
        self.assertEqual(trainer.next_level_xp, get_total_xp_for_level(101))
        self.assertEqual(trainer.max_hp, get_max_hp_for_level(100))
        self.assertEqual(trainer.current_hp, trainer.max_hp)

    def test_level_up_preserves_damage_while_increasing_hp(self):
        user = User.objects.create_user(username='hurtuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='HurtUser',
            gender='male',
            city='pallet_town',
            clan='orebound',
            current_hp=75,
            max_hp=100,
        )

        add_trainer_xp(trainer, get_total_xp_for_level(100))
        trainer.refresh_from_db()

        self.assertEqual(trainer.current_hp, trainer.max_hp - 25)


class TrainerProfileAccessTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('trainers:dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_user_without_profile_is_sent_to_profile_creation(self):
        user = User.objects.create_user(username='brock', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:dashboard'))

        self.assertRedirects(response, reverse('trainers:profile_create'))

    def test_profile_creation_belongs_to_logged_user(self):
        user = User.objects.create_user(username='leaf', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:profile_create'),
            {
                'trainer_name': 'Leaf',
                'gender': 'female',
                'city': 'pallet_town',
                'clan': 'naturia',
            },
        )

        self.assertRedirects(response, reverse('trainers:dashboard'))
        profile = TrainerProfile.objects.get(user=user)
        self.assertEqual(profile.trainer_name, 'Leaf')
        self.assertEqual(profile.level, 1)
        self.assertEqual(profile.next_level_xp, 98)
        self.assertEqual(profile.current_hp, 100)
        self.assertTrue(profile.inventory_initialized)
        self.assertEqual(profile.inventory_items.get(name='Poké Ball').quantity, 200)
        self.assertEqual(profile.inventory_items.get(name='Great Ball').quantity, 150)
        self.assertEqual(profile.inventory_items.get(name='Ultra Ball').quantity, 100)
        self.assertEqual(profile.inventory_items.get(name='Master Ball').quantity, 1)
        self.assertEqual(profile.inventory_items.get(name='Potion').quantity, 200)
        self.assertEqual(profile.inventory_items.get(name='Leaf Stone').quantity, 10)

    def test_user_with_profile_can_access_dashboard(self):
        user = User.objects.create_user(username='red', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='Red',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Red')
        self.assertContains(response, 'Outland Main')
        self.assertContains(response, '22.000.000 XP')
        self.assertContains(response, 'inventory-slot', count=40)

    def test_dashboard_shows_inventory_item_in_slot(self):
        user = User.objects.create_user(username='baguser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='BagUser',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        InventoryItem.objects.create(
            trainer=trainer,
            slot_number=3,
            name='Potion',
            quantity=4,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Potion')
        self.assertContains(response, 'x4')

    def test_inventory_item_can_be_removed(self):
        user = User.objects.create_user(username='removeitem', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='RemoveItem',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        item = InventoryItem.objects.create(
            trainer=trainer,
            slot_number=1,
            name='Potion',
            quantity=200,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:inventory_item_delete', args=[item.id])
        )

        self.assertRedirects(response, reverse('trainers:dashboard'))
        self.assertFalse(InventoryItem.objects.filter(id=item.id).exists())

    def test_registered_pokemon_can_be_added_to_team(self):
        user = User.objects.create_user(username='teamuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='TeamUser',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        PokedexRegistration.objects.create(trainer=trainer, pokemon_number=25)
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:team_member_update'),
            {'slot_number': 1, 'pokemon_number': 25},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['pokemon']['name'], 'Pikachu')
        self.assertTrue(
            TrainerTeamMember.objects.filter(
                trainer=trainer,
                slot_number=1,
                pokemon_number=25,
            ).exists()
        )

    def test_deposit_pokemon_can_be_added_to_team_with_action_post(self):
        user = User.objects.create_user(username='depositteam', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='DepositTeam',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        PokedexRegistration.objects.create(trainer=trainer, pokemon_number=25)
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:team_member_update'),
            {'action': 'add', 'pokemon_number': 25},
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'add')
        self.assertEqual(response.json()['slot_number'], 1)
        self.assertTrue(
            TrainerTeamMember.objects.filter(
                trainer=trainer,
                slot_number=1,
                pokemon_number=25,
            ).exists()
        )

    def test_deposit_pokemon_html_post_redirects_back_to_open_inventory(self):
        user = User.objects.create_user(username='depositfallback', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='DepositFallback',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        PokedexRegistration.objects.create(trainer=trainer, pokemon_number=25)
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:team_member_update'),
            {'action': 'add', 'pokemon_number': 25},
            HTTP_ACCEPT='text/html',
        )

        self.assertRedirects(
            response,
            f"{reverse('trainers:dashboard')}?inventory=open",
        )
        self.assertTrue(
            TrainerTeamMember.objects.filter(
                trainer=trainer,
                slot_number=1,
                pokemon_number=25,
            ).exists()
        )

    def test_unregistered_pokemon_cannot_be_added_to_team(self):
        user = User.objects.create_user(username='lockedteam', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='LockedTeam',
            gender='female',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:team_member_update'),
            {'slot_number': 1, 'pokemon_number': 25},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(TrainerTeamMember.objects.filter(trainer=trainer).exists())

    def test_team_slot_can_be_emptied(self):
        user = User.objects.create_user(username='emptyteam', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='EmptyTeam',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        TrainerTeamMember.objects.create(
            trainer=trainer,
            slot_number=1,
            pokemon_number=25,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:team_member_update'),
            {'slot_number': 1, 'pokemon_number': ''},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['pokemon'])
        self.assertFalse(TrainerTeamMember.objects.filter(trainer=trainer).exists())

    def test_mission_completion_adds_xp_to_active_trainer(self):
        user = User.objects.create_user(username='misty', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Misty',
            gender='female',
            city='cerulean_city',
            clan='seavel',
        )
        self.client.force_login(user)
        session = self.client.session
        session['active_trainer_id'] = trainer.id
        session.save()

        response = self.client.post(reverse('trainers:mission_complete', args=['mewtwo']))

        self.assertRedirects(response, reverse('trainers:dashboard'))
        trainer.refresh_from_db()
        self.assertEqual(trainer.current_xp, 1250000)
        self.assertEqual(trainer.level, get_level_for_total_xp(1250000))
        self.assertTrue(
            MissionCompletion.objects.filter(
                trainer=trainer,
                mission_key='mewtwo',
                xp_reward=1250000,
            ).exists()
        )

    def test_mission_completion_does_not_add_xp_twice(self):
        user = User.objects.create_user(username='surge', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Surge',
            gender='male',
            city='vermilion_city',
            clan='raibolt',
        )
        self.client.force_login(user)

        self.client.post(reverse('trainers:mission_complete', args=['celebi']))
        self.client.post(reverse('trainers:mission_complete', args=['celebi']))

        trainer.refresh_from_db()
        self.assertEqual(trainer.current_xp, 950000)
        self.assertEqual(
            MissionCompletion.objects.filter(trainer=trainer, mission_key='celebi').count(),
            1,
        )

    def test_pokedex_search_requires_profile(self):
        user = User.objects.create_user(username='blue', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:pokedex_search'), {'q': 'pika'})

        self.assertEqual(response.status_code, 403)

    def test_pokedex_search_returns_matching_pokemon(self):
        user = User.objects.create_user(username='yellow', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='Yellow',
            gender='female',
            city='viridian_city',
            clan='raibolt',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:pokedex_search'), {'q': 'pika'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['name'], 'Pikachu')

    def test_pokedex_empty_search_returns_first_649_pokemon_as_unregistered(self):
        user = User.objects.create_user(username='may', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='May',
            gender='female',
            city='pallet_town',
            clan='seavel',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:pokedex_search'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 649)
        self.assertEqual(payload['results'][648]['number'], 649)
        self.assertFalse(payload['results'][0]['registered'])
        self.assertEqual(payload['registered_count'], 0)

    def test_pokedex_registered_filter_returns_only_registered_pokemon(self):
        user = User.objects.create_user(username='iris', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Iris',
            gender='female',
            city='pallet_town',
            clan='naturia',
        )
        PokedexRegistration.objects.create(trainer=trainer, pokemon_number=25)
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:pokedex_search'), {'registered': '1'})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['name'], 'Pikachu')
        self.assertTrue(payload['results'][0]['registered'])

    def test_pokedex_register_marks_pokemon_for_active_trainer(self):
        user = User.objects.create_user(username='cilan', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Cilan',
            gender='male',
            city='pallet_town',
            clan='naturia',
        )
        self.client.force_login(user)
        session = self.client.session
        session['active_trainer_id'] = trainer.id
        session.save()

        response = self.client.post(
            reverse('trainers:pokedex_register'),
            {'pokemon_name': 'Genesect'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            PokedexRegistration.objects.filter(
                trainer=trainer,
                pokemon_number=649,
            ).exists()
        )

    def test_pokedex_register_form_posts_and_persists_without_ajax(self):
        user = User.objects.create_user(username='noajax', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='NoAjax',
            gender='male',
            city='pallet_town',
            clan='naturia',
        )
        self.client.force_login(user)
        session = self.client.session
        session['active_trainer_id'] = trainer.id
        session.save()

        response = self.client.post(
            reverse('trainers:pokedex_register'),
            {'pokemon_name': 'Pikachu'},
            HTTP_ACCEPT='text/html',
        )

        self.assertRedirects(
            response,
            f"{reverse('trainers:dashboard')}?pokedex=open",
        )
        self.assertTrue(
            PokedexRegistration.objects.filter(
                trainer=trainer,
                pokemon_number=25,
            ).exists()
        )

    def test_friends_page_lists_empty_state(self):
        user = User.objects.create_user(username='bianca', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='Bianca',
            gender='female',
            city='pallet_town',
            clan='seavel',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:friends'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nenhum amigo registrado ainda.')

    def test_friends_post_adds_friend(self):
        user = User.objects.create_user(username='cheren', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Cheren',
            gender='male',
            city='pallet_town',
            clan='ironheart',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:friends'),
            {
                'name': 'Bianca',
                'nickname': 'Bia',
                'clan': 'naturia',
                'city': 'pallet_town',
                'level': 42,
                'notes': 'Parceira de batalhas.',
            },
        )

        self.assertRedirects(response, reverse('trainers:friends'))
        friend = Friend.objects.get(trainer=trainer, name='Bianca', status='added')
        self.assertEqual(friend.nickname, 'Bia')
        self.assertEqual(friend.clan, 'naturia')
        self.assertEqual(friend.level, 42)

    def test_friends_can_be_filtered_by_clan(self):
        user = User.objects.create_user(username='filterfriends', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='FilterFriends',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        Friend.objects.create(
            trainer=trainer,
            name='Kanto Friend',
            nickname='Kanto',
            clan='raibolt',
            city='vermilion_city',
            level=30,
        )
        Friend.objects.create(
            trainer=trainer,
            name='Johto Friend',
            nickname='Johto',
            clan='naturia',
            city='celadon_city',
            level=35,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse('trainers:friends'),
            {'clan': 'raibolt'},
        )

        self.assertContains(response, 'Kanto Friend')
        self.assertNotContains(response, 'Johto Friend')

    def test_friend_invite_updates_existing_friend(self):
        user = User.objects.create_user(username='shauna', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Shauna',
            gender='female',
            city='pallet_town',
            clan='gardestrike',
        )
        friend = Friend.objects.create(trainer=trainer, name='Tierno', contact='tierno#002')
        self.client.force_login(user)

        response = self.client.post(reverse('trainers:friend_invite', args=[friend.id]))

        self.assertRedirects(response, reverse('trainers:friends'))
        friend.refresh_from_db()
        self.assertEqual(friend.status, 'invited')

    def test_friend_delete_uses_active_trainer(self):
        user = User.objects.create_user(username='trevor', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='Trevor',
            gender='male',
            city='pallet_town',
            clan='psycraft',
        )
        friend = Friend.objects.create(trainer=trainer, name='Serena')
        self.client.force_login(user)

        response = self.client.delete(reverse('trainers:friend_delete', args=[friend.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Friend.objects.filter(id=friend.id).exists())

    def test_profile_update_changes_name_clan_and_city(self):
        user = User.objects.create_user(username='dawn', password='StrongPass123!')
        profile = TrainerProfile.objects.create(
            user=user,
            trainer_name='Dawn',
            gender='female',
            city='pallet_town',
            clan='seavel',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:profile_update'),
            {
                'trainer_name': 'Dawn Nova',
                'city': 'saffron_city',
                'clan': 'psycraft',
            },
        )

        self.assertRedirects(response, reverse('trainers:dashboard'))
        profile.refresh_from_db()
        self.assertEqual(profile.trainer_name, 'Dawn Nova')
        self.assertEqual(profile.city, 'saffron_city')
        self.assertEqual(profile.clan, 'psycraft')

    def test_profile_update_requires_existing_profile(self):
        user = User.objects.create_user(username='silver', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:profile_update'),
            {
                'trainer_name': 'Silver',
                'city': 'viridian_city',
                'clan': 'malefic',
            },
        )

        self.assertRedirects(response, reverse('trainers:profile_create'))

    def test_password_update_changes_logged_user_password(self):
        user = User.objects.create_user(username='brendan', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='Brendan',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:password_update'),
            {
                'old_password': 'StrongPass123!',
                'new_password1': 'NewStrongPass123!',
                'new_password2': 'NewStrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('trainers:dashboard'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewStrongPass123!'))

    def test_user_can_create_more_than_one_trainer_profile(self):
        user = User.objects.create_user(username='hilbert', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='Hilbert',
            gender='male',
            city='pallet_town',
            clan='ironheart',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('trainers:profile_create'),
            {
                'trainer_name': 'Hilda',
                'gender': 'female',
                'city': 'celadon_city',
                'clan': 'naturia',
            },
        )

        self.assertRedirects(response, reverse('trainers:dashboard'))
        self.assertEqual(user.trainer_profiles.count(), 2)
        self.assertEqual(
            self.client.session['active_trainer_id'],
            user.trainer_profiles.get(trainer_name='Hilda').id,
        )

    def test_dashboard_uses_selected_trainer(self):
        user = User.objects.create_user(username='rosa', password='StrongPass123!')
        first = TrainerProfile.objects.create(
            user=user,
            trainer_name='Rosa',
            gender='female',
            city='pallet_town',
            clan='seavel',
        )
        second = TrainerProfile.objects.create(
            user=user,
            trainer_name='Nate',
            gender='male',
            city='saffron_city',
            clan='psycraft',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('trainers:profile_select', args=[second.id]))

        self.assertRedirects(response, reverse('trainers:dashboard'))
        self.assertNotEqual(first.id, self.client.session['active_trainer_id'])
        self.assertEqual(second.id, self.client.session['active_trainer_id'])

    def test_user_cannot_select_trainer_from_another_account(self):
        user = User.objects.create_user(username='calem', password='StrongPass123!')
        other_user = User.objects.create_user(username='serena', password='StrongPass123!')
        other_trainer = TrainerProfile.objects.create(
            user=other_user,
            trainer_name='Serena',
            gender='female',
            city='celadon_city',
            clan='gardestrike',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('trainers:profile_select', args=[other_trainer.id]))

        self.assertEqual(response.status_code, 404)

    def test_first_trainer_cannot_be_deleted(self):
        user = User.objects.create_user(username='firstsafe', password='StrongPass123!')
        first = TrainerProfile.objects.create(
            user=user,
            trainer_name='FirstSafe',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('trainers:profile_delete', args=[first.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(TrainerProfile.objects.filter(id=first.id).exists())

    def test_secondary_trainer_can_be_deleted(self):
        user = User.objects.create_user(username='deleteextra', password='StrongPass123!')
        first = TrainerProfile.objects.create(
            user=user,
            trainer_name='First',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        second = TrainerProfile.objects.create(
            user=user,
            trainer_name='Second',
            gender='female',
            city='cerulean_city',
            clan='seavel',
        )
        self.client.force_login(user)
        session = self.client.session
        session['active_trainer_id'] = second.id
        session.save()

        response = self.client.post(reverse('trainers:profile_delete', args=[second.id]))

        self.assertRedirects(response, reverse('trainers:dashboard'))
        self.assertFalse(TrainerProfile.objects.filter(id=second.id).exists())
        self.assertEqual(self.client.session['active_trainer_id'], first.id)

    def test_public_home_accessible_without_login(self):
        """Requisito: Home aberta e navegavel sem credenciais."""
        response = self.client.get(reverse('trainers:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'trainers/home.html')
        self.assertContains(response, 'TrainerDex')
        self.assertContains(response, 'Área Pública Aberta')

    def test_protected_routes_redirect_to_login(self):
        """Requisito: Acessar modulos internos redireciona automaticamente para /login/."""
        for url_name in ['trainers:dashboard', 'trainers:friends', 'trainers:profile_create']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('accounts:login'), response['Location'])

    def test_friend_crud_update_view(self):
        """Requisito: CRUD completo com ModelForm (Update em Friend)."""
        user = User.objects.create_user(username='cruduser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='CrudTrainer',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        friend = Friend.objects.create(
            trainer=trainer,
            name='Brock',
            nickname='Pedra',
            clan='orebound',
            city='pewter_city',
            level=15,
            notes='Líder de ginásio',
        )
        self.client.force_login(user)

        # GET friend_update
        response = self.client.get(reverse('trainers:friend_update', args=[friend.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'trainers/friend_form.html')
        self.assertContains(response, 'Brock')

        # POST friend_update
        update_data = {
            'name': 'Brock Pewter',
            'nickname': 'Mestre Pedra',
            'clan': 'orebound',
            'city': 'pewter_city',
            'level': 20,
            'notes': 'Líder experiente',
        }
        post_response = self.client.post(reverse('trainers:friend_update', args=[friend.id]), update_data)
        self.assertRedirects(post_response, reverse('trainers:friends'))
        friend.refresh_from_db()
        self.assertEqual(friend.name, 'Brock Pewter')
        self.assertEqual(friend.nickname, 'Mestre Pedra')
        self.assertEqual(friend.level, 20)

    def test_friend_report_export_csv(self):
        """Requisito: Tela de consultas com filtros e geracao/exportacao de relatorio."""
        user = User.objects.create_user(username='reportuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='ReportTrainer',
            gender='female',
            city='cerulean_city',
            clan='seavel',
        )
        Friend.objects.create(
            trainer=trainer,
            name='Misty',
            nickname='Aquatica',
            clan='seavel',
            city='cerulean_city',
            level=18,
            status='added',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:friends_report_export'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Nome;Apelido;Clã;Cidade;Nível;Status', content)
        self.assertIn('Misty;Aquatica', content)

    def test_models_relationships_1_to_1_and_n_to_n_through(self):
        """Requisito: Relacionamentos 1:1 e N:N com tabela intermediaria through."""
        from trainers.models import Mission, MissionCompletion, TrainerCard

        user = User.objects.create_user(username='reluser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='RelTrainer',
            gender='male',
            city='viridian_city',
            clan='naturia',
        )

        # 1:1 (TrainerProfile <-> TrainerCard)
        card = trainer.get_or_create_card()
        self.assertIsInstance(card, TrainerCard)
        self.assertEqual(card.trainer, trainer)
        self.assertEqual(trainer.card, card)

        # N:N with through (TrainerProfile <-> Mission through MissionCompletion)
        mission = Mission.objects.create(key='test-quest', title='Busca Lendária', xp_reward=5000)
        completion = MissionCompletion.objects.create(
            trainer=trainer,
            mission=mission,
            mission_key=mission.key,
            xp_reward=5000,
        )
        self.assertIn(mission, trainer.completed_missions.all())
        self.assertIn(trainer, mission.completed_by_trainers.all())
        self.assertEqual(completion.mission, mission)
        self.assertEqual(completion.trainer, trainer)

    def test_dashboard_indicators_aggregated_from_database(self):
        """Requisito: Dashboard com indicadores reais agregados do banco de dados (Count, Sum, Avg)."""
        user = User.objects.create_user(username='dashuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='StatsTrainer',
            gender='female',
            city='vermilion_city',
            clan='raibolt',
        )
        Friend.objects.create(trainer=trainer, name='LtSurge', nickname='Trovão', clan='raibolt', city='vermilion_city', level=30)
        Friend.objects.create(trainer=trainer, name='Volkner', nickname='Raio', clan='raibolt', city='vermilion_city', level=40)
        self.client.force_login(user)

        response = self.client.get(reverse('trainers:dashboard'))
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        self.assertEqual(stats['friends_count'], 2)
        self.assertEqual(stats['friends_avg_level'], 35.0)
        self.assertIn('stats', response.context)
        self.assertContains(response, 'Indicadores agregados do banco de dados')

    def test_pokedex_crud_lifecycle(self):
        """CRUD Pokédex completo: Criar, Listar, Atualizar e Excluir registro de Pokémon."""
        user = User.objects.create_user(username='pkuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='DexMaster',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        # 1. CREATE via pokedex_page POST
        post_data = {
            'pokemon_number': 25,
            'nickname': 'PikaPika',
            'notes': 'Capturado no bosque de Viridian',
            'is_favorite': True,
        }
        res_create = self.client.post(reverse('trainers:pokedex'), post_data)
        self.assertRedirects(res_create, reverse('trainers:pokedex'))
        registration = trainer.pokedex_registrations.get(pokemon_number=25)
        self.assertEqual(registration.nickname, 'PikaPika')
        self.assertTrue(registration.is_favorite)

        # 2. READ via pokedex_page GET
        res_read = self.client.get(reverse('trainers:pokedex'))
        self.assertEqual(res_read.status_code, 200)
        self.assertTemplateUsed(res_read, 'trainers/pokedex.html')
        self.assertContains(res_read, 'PikaPika')
        self.assertContains(res_read, 'Pikachu')

        # 3. UPDATE via pokedex_update GET & POST
        res_edit_get = self.client.get(reverse('trainers:pokedex_update', args=[registration.id]))
        self.assertEqual(res_edit_get.status_code, 200)
        self.assertTemplateUsed(res_edit_get, 'trainers/pokedex_form.html')

        update_data = {
            'nickname': 'Sparky Gold',
            'notes': 'Treinado até a perfeição elétrica',
            'is_favorite': True,
        }
        res_edit_post = self.client.post(reverse('trainers:pokedex_update', args=[registration.id]), update_data)
        self.assertRedirects(res_edit_post, reverse('trainers:pokedex'))
        registration.refresh_from_db()
        self.assertEqual(registration.nickname, 'Sparky Gold')
        self.assertEqual(registration.notes, 'Treinado até a perfeição elétrica')

        # 4. DELETE via pokedex_delete POST
        res_delete = self.client.post(reverse('trainers:pokedex_delete', args=[registration.id]))
        self.assertRedirects(res_delete, reverse('trainers:pokedex'))
        self.assertFalse(trainer.pokedex_registrations.filter(pokemon_number=25).exists())

    def test_profile_crud_dedicated_page(self):
        """CRUD Perfil: visualização e gestão dedicada de perfis do treinador."""
        user = User.objects.create_user(username='profuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='ProfileLead',
            gender='female',
            city='cerulean_city',
            clan='seavel',
        )
        self.client.force_login(user)

        res = self.client.get(reverse('trainers:profile_detail'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'trainers/profile_page.html')
        self.assertContains(res, 'ProfileLead')
        self.assertContains(res, 'Código da Licença')
        self.assertIn('trainer_card', res.context)
        self.assertIn('profile_form', res.context)

    def test_dashboard_buttons_link_to_dedicated_cruds(self):
        """Os botoes de Perfil e Pokedex no dashboard redirecionam diretamente para as rotas dos seus CRUDs."""
        user = User.objects.create_user(username='navuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='NavTrainer',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        res = self.client.get(reverse('trainers:dashboard'))
        self.assertEqual(res.status_code, 200)

        # Verifica que o botao de Perfil aponta para o CRUD de perfil
        self.assertContains(res, f'href="{reverse("trainers:profile_detail")}"')
        # Verifica que o botao de Pokedex aponta para o CRUD da pokedex
        self.assertContains(res, f'href="{reverse("trainers:pokedex")}"')

        # Verifica que os modais foram removidos do dashboard
        self.assertNotContains(res, 'data-profile-modal')
        self.assertNotContains(res, 'data-pokedex-modal')

    def test_dashboard_removes_pokedex_and_profile_from_menu_grid_keeping_top_nav(self):
        """Dashboard remove os cards de Perfil e Pokédex do menu-grid, mantendo-os no top-nav."""
        user = User.objects.create_user(username='gridnavuser', password='StrongPass123!')
        TrainerProfile.objects.create(
            user=user,
            trainer_name='GridNavTrainer',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        res = self.client.get(reverse('trainers:dashboard'))
        self.assertEqual(res.status_code, 200)

        # No top-nav:
        self.assertContains(res, 'class="nav-tab-item">Pokédex</a>')
        self.assertContains(res, 'class="nav-tab-item">Perfil</a>')

        # No menu-grid: Perfil e Pokedex foram removidos dos cards, restando Mochila e Missões
        content = res.content.decode('utf-8')
        menu_grid_idx = content.find('class="menu-grid"')
        menu_grid_end = content.find('</section>', menu_grid_idx)
        menu_grid_html = content[menu_grid_idx:menu_grid_end]
        self.assertNotIn('Perfil', menu_grid_html)
        self.assertNotIn('Pokédex', menu_grid_html)
        self.assertIn('data-inventory-open', menu_grid_html)
        self.assertIn('data-missions-open', menu_grid_html)

    def test_pokedex_registration_by_name(self):
        """Cadastro de Pokémon na Pokédex feito pelo nome ao invés de número."""
        user = User.objects.create_user(username='pknameuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='PkNameTrainer',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        self.client.force_login(user)

        res = self.client.post(reverse('trainers:pokedex'), {
            'pokemon_name': 'Charmander',
            'nickname': 'Flame',
            'notes': 'Capturado perto do vulcão',
            'is_favorite': True,
        })
        self.assertRedirects(res, reverse('trainers:pokedex'))
        self.assertTrue(trainer.pokedex_registrations.filter(pokemon_number=4).exists())

    def test_friends_details_without_nickname(self):
        """No CRUD de amigos, a parte de dados do amigo não exibe campo de apelido."""
        user = User.objects.create_user(username='nonickuser', password='StrongPass123!')
        trainer = TrainerProfile.objects.create(
            user=user,
            trainer_name='NoNickTrainer',
            gender='male',
            city='pallet_town',
            clan='orebound',
        )
        friend = Friend.objects.create(
            trainer=trainer,
            name='Misty',
            clan='seavel',
            city='cerulean_city',
            level=25,
            notes='Especialista em água',
        )
        self.client.force_login(user)

        res = self.client.get(reverse('trainers:friends'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Misty')
        self.assertContains(res, 'Clã:')
        self.assertContains(res, 'Cidade:')
        self.assertContains(res, 'Nível:')
        # Não exibe campo ou detalhe de Apelido nos dados do amigo
        content = res.content.decode('utf-8')
        friend_card_idx = content.find('data-friend-card')
        friend_card_end = content.find('</article>', friend_card_idx)
        card_html = content[friend_card_idx:friend_card_end]
        self.assertNotIn('Apelido:', card_html)
