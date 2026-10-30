from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import FriendForm, TrainerProfileForm, TrainerProfileUpdateForm
from .models import Friend, PokedexRegistration, TrainerProfile, TrainerTeamMember
from .services.experience import get_level_progress, sync_trainer_experience
from .services.inventory import (
    get_inventory_slots,
    get_pokemon_deposit,
    get_team_slots,
    initialize_trainer_inventory,
)
from .services.missions import complete_mission_for_trainer, get_missions_for_trainer
from .services.pokedex import find_pokemon_by_name, find_pokemon_by_number, search_pokemon


@login_required
def dashboard(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    xp_progress = sync_trainer_experience(active_trainer)

    context = {
        'active_trainer': active_trainer,
        'xp_progress': xp_progress,
        'inventory_slots': get_inventory_slots(active_trainer),
        'team_slots': get_team_slots(active_trainer),
        'pokemon_deposit': get_pokemon_deposit(active_trainer),
        'registered_pokemon': [
            find_pokemon_by_number(number)
            for number in active_trainer.pokedex_registrations.values_list(
                'pokemon_number', flat=True
            )
            if find_pokemon_by_number(number)
        ],
        'missions': get_missions_for_trainer(active_trainer),
        'trainer_profiles': request.user.trainer_profiles.all(),
        'profile_form': TrainerProfileUpdateForm(instance=active_trainer),
        'create_profile_form': TrainerProfileForm(),
        'password_form': PasswordChangeForm(request.user),
    }
    return render(request, 'trainers/dashboard.html', context)


@login_required
@require_POST
def mission_complete(request, mission_key):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return JsonResponse({'error': 'Personagem ativo nao encontrado.'}, status=403)

    completion, created, progress = complete_mission_for_trainer(active_trainer, mission_key)
    if completion is None:
        return JsonResponse({'error': 'Missao nao encontrada.'}, status=404)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        active_trainer.refresh_from_db()
        xp_progress = get_level_progress(active_trainer.current_xp)
        return JsonResponse({
            'completed': True,
            'created': created,
            'level': active_trainer.level,
            'current_xp': active_trainer.current_xp,
            'xp_progress': xp_progress,
        })

    return redirect('trainers:dashboard')


@login_required
def profile_create(request):
    if request.method == 'POST':
        form = TrainerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.next_level_xp = get_level_progress(profile.current_xp)['next_level_xp']
            profile.save()
            initialize_trainer_inventory(profile)
            request.session['active_trainer_id'] = profile.id
            return redirect('trainers:dashboard')
    else:
        form = TrainerProfileForm()

    return render(request, 'trainers/profile_form.html', {'form': form})


@login_required
@require_POST
def team_member_update(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return JsonResponse({'error': 'Personagem ativo nao encontrado.'}, status=403)

    action = request.POST.get('action', '').strip()
    pokemon_value = request.POST.get('pokemon_number', '').strip()

    if action in {'add', 'remove'}:
        try:
            pokemon_number = int(pokemon_value)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Pokemon invalido.'}, status=400)

        pokemon = find_pokemon_by_number(pokemon_number)
        if pokemon is None:
            return JsonResponse({'error': 'Pokemon invalido.'}, status=400)

        if action == 'remove':
            member = TrainerTeamMember.objects.filter(
                trainer=active_trainer,
                pokemon_number=pokemon_number,
            ).first()
            if member is None:
                return JsonResponse({'error': 'Este Pokemon nao esta na equipe.'}, status=400)
            slot_number = member.slot_number
            member.delete()
            if not _wants_json(request):
                return redirect(f"{reverse('trainers:dashboard')}?inventory=open")
            return JsonResponse({
                'action': 'remove',
                'slot_number': slot_number,
                'pokemon': pokemon,
            })

        if not active_trainer.pokedex_registrations.filter(
            pokemon_number=pokemon_number
        ).exists():
            return JsonResponse(
                {'error': 'Registre este Pokemon na Pokedex antes de usa-lo.'},
                status=400,
            )
        if active_trainer.team_members.filter(pokemon_number=pokemon_number).exists():
            return JsonResponse({'error': 'Este Pokemon ja esta na equipe.'}, status=400)

        occupied_slots = set(
            active_trainer.team_members.values_list('slot_number', flat=True)
        )
        slot_number = next(
            (number for number in range(1, 7) if number not in occupied_slots),
            None,
        )
        if slot_number is None:
            return JsonResponse(
                {'error': 'A equipe ja esta completa. Remova um Pokemon primeiro.'},
                status=400,
            )
        TrainerTeamMember.objects.create(
            trainer=active_trainer,
            slot_number=slot_number,
            pokemon_number=pokemon_number,
        )
        if not _wants_json(request):
            return redirect(f"{reverse('trainers:dashboard')}?inventory=open")
        return JsonResponse({
            'action': 'add',
            'slot_number': slot_number,
            'pokemon': pokemon,
        })

    try:
        slot_number = int(request.POST.get('slot_number', ''))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Slot da equipe invalido.'}, status=400)

    if slot_number not in range(1, 7):
        return JsonResponse({'error': 'Slot da equipe invalido.'}, status=400)

    if not pokemon_value:
        TrainerTeamMember.objects.filter(
            trainer=active_trainer,
            slot_number=slot_number,
        ).delete()
        return JsonResponse({'slot_number': slot_number, 'pokemon': None})

    try:
        pokemon_number = int(pokemon_value)
    except ValueError:
        return JsonResponse({'error': 'Pokemon invalido.'}, status=400)

    if not active_trainer.pokedex_registrations.filter(
        pokemon_number=pokemon_number
    ).exists():
        return JsonResponse(
            {'error': 'Registre este Pokemon na Pokedex antes de coloca-lo na equipe.'},
            status=400,
        )

    duplicate = TrainerTeamMember.objects.filter(
        trainer=active_trainer,
        pokemon_number=pokemon_number,
    ).exclude(slot_number=slot_number)
    if duplicate.exists():
        return JsonResponse({'error': 'Este Pokemon ja esta na equipe.'}, status=400)

    pokemon = find_pokemon_by_number(pokemon_number)
    if pokemon is None:
        return JsonResponse({'error': 'Pokemon invalido.'}, status=400)

    TrainerTeamMember.objects.update_or_create(
        trainer=active_trainer,
        slot_number=slot_number,
        defaults={'pokemon_number': pokemon_number},
    )
    return JsonResponse({'slot_number': slot_number, 'pokemon': pokemon})


@login_required
@require_POST
def inventory_item_delete(request, item_id):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    item = get_object_or_404(active_trainer.inventory_items, id=item_id)
    item.delete()
    return redirect('trainers:dashboard')


@login_required
def pokedex_search(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return JsonResponse({'results': []}, status=403)

    query = request.GET.get('q', '')
    registered_only = request.GET.get('registered') == '1'
    registered_numbers = set(
        active_trainer.pokedex_registrations.values_list('pokemon_number', flat=True)
    )
    return JsonResponse({
        'results': search_pokemon(query, registered_numbers, registered_only),
        'registered_count': len(registered_numbers),
        'total_count': 649,
    })


@login_required
@require_POST
def pokedex_register(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return JsonResponse({'error': 'Personagem ativo nao encontrado.'}, status=403)

    pokemon = find_pokemon_by_name(request.POST.get('pokemon_name', ''))
    if pokemon is None:
        return JsonResponse({'error': 'Pokemon nao encontrado pelo nome informado.'}, status=400)

    PokedexRegistration.objects.get_or_create(
        trainer=active_trainer,
        pokemon_number=pokemon['number'],
    )

    if not _wants_json(request):
        return redirect(f"{reverse('trainers:dashboard')}?pokedex=open")

    registered_numbers = set(
        active_trainer.pokedex_registrations.values_list('pokemon_number', flat=True)
    )
    return JsonResponse({
        'registered': True,
        'pokemon_number': pokemon['number'],
        'pokemon_name': pokemon['name'],
        'pokemon': pokemon,
        'registered_count': len(registered_numbers),
        'total_count': 649,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def friends_page(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    if request.method == 'POST':
        friend_form = FriendForm(request.POST)
        if friend_form.is_valid():
            if active_trainer.friends.filter(name__iexact=friend_form.cleaned_data['name']).exists():
                friend_form.add_error('name', 'Este amigo já foi adicionado.')
            else:
                friend = friend_form.save(commit=False)
                friend.trainer = active_trainer
                friend.save()
                return redirect('trainers:friends')
    else:
        friend_form = FriendForm()

    friends = active_trainer.friends.all()
    selected_clan = request.GET.get('clan', '').strip()
    if selected_clan:
        friends = friends.filter(clan=selected_clan)

    return render(
        request,
        'trainers/friends.html',
        {
            'active_trainer': active_trainer,
            'friends': friends,
            'friend_form': friend_form,
            'clan_choices': TrainerProfile.CLAN_CHOICES,
            'selected_clan': selected_clan,
        },
    )


@login_required
@require_POST
def friend_invite(request, friend_id):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    friend = get_object_or_404(active_trainer.friends, id=friend_id)
    friend.status = 'invited'
    friend.save(update_fields=['status'])
    return redirect('trainers:friends')


@login_required
@require_http_methods(['DELETE', 'POST'])
def friend_delete(request, friend_id):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return JsonResponse({'error': 'Personagem ativo nao encontrado.'}, status=403)

    friend = get_object_or_404(active_trainer.friends, id=friend_id)
    friend.delete()

    if request.method == 'DELETE':
        return JsonResponse({'deleted': True})
    return redirect('trainers:friends')


@login_required
def profile_update(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    if request.method != 'POST':
        return redirect('trainers:dashboard')

    form = TrainerProfileUpdateForm(request.POST, instance=active_trainer)
    if form.is_valid():
        form.save()

    return redirect('trainers:dashboard')


@login_required
def password_update(request):
    if _get_active_trainer(request) is None:
        return redirect('trainers:profile_create')

    if request.method != 'POST':
        return redirect('trainers:dashboard')

    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)

    return redirect('trainers:dashboard')


@login_required
def profile_select(request, profile_id):
    trainer = get_object_or_404(
        request.user.trainer_profiles,
        id=profile_id,
    )
    request.session['active_trainer_id'] = trainer.id
    return redirect('trainers:dashboard')


@login_required
@require_POST
def profile_delete(request, profile_id):
    profiles = request.user.trainer_profiles.all()
    first_profile = profiles.first()
    trainer = get_object_or_404(profiles, id=profile_id)

    if first_profile and trainer.id == first_profile.id:
        return JsonResponse(
            {'error': 'O primeiro personagem da conta nao pode ser excluido.'},
            status=403,
        )

    was_active = request.session.get('active_trainer_id') == trainer.id
    trainer.delete()
    if was_active:
        remaining_profile = request.user.trainer_profiles.first()
        if remaining_profile:
            request.session['active_trainer_id'] = remaining_profile.id
        else:
            request.session.pop('active_trainer_id', None)

    return redirect('trainers:dashboard')


def _get_active_trainer(request):
    profiles = request.user.trainer_profiles.all()
    if not profiles.exists():
        request.session.pop('active_trainer_id', None)
        return None

    active_id = request.session.get('active_trainer_id')
    if active_id:
        trainer = profiles.filter(id=active_id).first()
        if trainer:
            return trainer

    trainer = profiles.first()
    request.session['active_trainer_id'] = trainer.id
    return trainer


def _wants_json(request):
    accept_header = request.headers.get('accept', '')
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or not accept_header
        or 'application/json' in accept_header
    )
