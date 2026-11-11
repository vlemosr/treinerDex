import csv
from io import StringIO

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    FriendForm,
    PokedexRegistrationForm,
    PokedexRegistrationUpdateForm,
    TrainerProfileForm,
    TrainerProfileUpdateForm,
)
from .models import Friend, PokedexRegistration, TrainerProfile, TrainerTeamMember
from .services.experience import get_level_progress, sync_trainer_experience
from .services.inventory import (
    get_inventory_slots,
    get_pokemon_deposit,
    get_team_slots,
    initialize_trainer_inventory,
)
from .services.missions import complete_mission_for_trainer, get_missions_for_trainer
from .services.pokedex import (
    find_pokemon_by_name,
    find_pokemon_by_number,
    get_all_pokemon_names,
    search_pokemon,
)


def home(request):
    return render(request, 'trainers/home.html')


@login_required
def dashboard(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    xp_progress = sync_trainer_experience(active_trainer)

    stats = {
        'total_inventory_items': active_trainer.inventory_items.aggregate(total=Sum('quantity'))['total'] or 0,
        'unique_inventory_slots': active_trainer.inventory_items.aggregate(count=Count('id'))['count'] or 0,
        'team_count': active_trainer.team_members.aggregate(count=Count('id'))['count'] or 0,
        'pokedex_count': active_trainer.pokedex_registrations.aggregate(count=Count('id'))['count'] or 0,
        'missions_completed_count': active_trainer.mission_completions.aggregate(count=Count('id'))['count'] or 0,
        'missions_xp_total': active_trainer.mission_completions.aggregate(total_xp=Sum('xp_reward'))['total_xp'] or 0,
        'friends_count': active_trainer.friends.aggregate(count=Count('id'))['count'] or 0,
        'friends_avg_level': round(active_trainer.friends.aggregate(avg=Avg('level'))['avg'] or 0, 1),
    }

    context = {
        'active_trainer': active_trainer,
        'trainer_card': active_trainer.get_or_create_card(),
        'stats': stats,
        'xp_progress': xp_progress,
        'inventory_slots': get_inventory_slots(active_trainer),
        'team_slots': get_team_slots(active_trainer),
        'pokemon_deposit': get_pokemon_deposit(active_trainer),
        'missions': get_missions_for_trainer(active_trainer),
        'trainer_profiles': request.user.trainer_profiles.all(),
        'create_profile_form': TrainerProfileForm(),
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


def _filter_friends(friends_qs, params):
    """Auxiliar compartilhado para filtrar queryset de amigos."""
    selected_clan = params.get('clan', '').strip()
    selected_city = params.get('city', '').strip()
    selected_status = params.get('status', '').strip()
    query = params.get('q', '').strip()

    if selected_clan:
        friends_qs = friends_qs.filter(clan=selected_clan)
    if selected_city:
        friends_qs = friends_qs.filter(city=selected_city)
    if selected_status:
        friends_qs = friends_qs.filter(status=selected_status)
    if query:
        friends_qs = friends_qs.filter(Q(name__icontains=query) | Q(nickname__icontains=query))

    return friends_qs, {
        'selected_clan': selected_clan,
        'selected_city': selected_city,
        'selected_status': selected_status,
        'query': query,
    }


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

    friends, filter_context = _filter_friends(active_trainer.friends.all(), request.GET)

    context = {
        'active_trainer': active_trainer,
        'friends': friends,
        'friend_form': friend_form,
        'clan_choices': TrainerProfile.CLAN_CHOICES,
        'city_choices': TrainerProfile.CITY_CHOICES,
        **filter_context,
    }
    return render(request, 'trainers/friends.html', context)


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
def friend_update(request, friend_id):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    friend = get_object_or_404(active_trainer.friends, id=friend_id)

    if request.method == 'POST':
        form = FriendForm(request.POST, instance=friend)
        if form.is_valid():
            form.save()
            return redirect('trainers:friends')
    else:
        form = FriendForm(instance=friend)

    return render(
        request,
        'trainers/friend_form.html',
        {
            'active_trainer': active_trainer,
            'friend': friend,
            'form': form,
        },
    )


@login_required
def friends_report_export(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    friends, _ = _filter_friends(active_trainer.friends.all(), request.GET)

    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Nome',
        'Apelido',
        'Clã',
        'Cidade',
        'Nível',
        'Status',
        'Data de Registro',
        'Observações',
    ])

    for friend in friends:
        writer.writerow([
            friend.name,
            friend.nickname or '-',
            friend.get_clan_display() if hasattr(friend, 'get_clan_display') else friend.clan,
            friend.get_city_display() if hasattr(friend, 'get_city_display') else friend.city,
            friend.level,
            friend.get_status_display(),
            friend.created_at.strftime('%d/%m/%Y %H:%M') if friend.created_at else '-',
            friend.notes.replace('\n', ' ') if friend.notes else '',
        ])

    csv_data = '\ufeff' + output.getvalue()
    response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8')
    filename = f'relatorio_amigos_{active_trainer.trainer_name}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


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

    next_url = request.POST.get('next')
    form = TrainerProfileUpdateForm(request.POST, instance=active_trainer)
    if form.is_valid():
        form.save()
        if next_url:
            return redirect(next_url)
        return redirect('trainers:dashboard')

    if next_url:
        return redirect(next_url)
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


@login_required
def pokedex_page(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    if request.method == 'POST':
        form = PokedexRegistrationForm(request.POST)
        if form.is_valid():
            pkmn = getattr(form, 'cleaned_pokemon', None)
            num = pkmn['number'] if pkmn else getattr(form.instance, 'pokemon_number', None)
            name = pkmn['name'] if pkmn else f'#{num}'
            if num and active_trainer.pokedex_registrations.filter(pokemon_number=num).exists():
                form.add_error('pokemon_name', f'O Pokémon {name} já está registrado na sua Pokédex.')
            elif not num or not find_pokemon_by_number(num):
                form.add_error('pokemon_name', f'Pokémon {name} não encontrado no catálogo.')
            else:
                reg = form.save(commit=False)
                reg.trainer = active_trainer
                reg.pokemon_number = num
                reg.save()
                return redirect('trainers:pokedex')
    else:
        form = PokedexRegistrationForm()

    query = request.GET.get('q', '').strip().lower()
    only_favorite = request.GET.get('favorite', '') == '1'

    registrations = active_trainer.pokedex_registrations.all().order_by('pokemon_number')
    if only_favorite:
        registrations = registrations.filter(is_favorite=True)

    items = []
    for reg in registrations:
        pkmn = find_pokemon_by_number(reg.pokemon_number) or {
            'number': reg.pokemon_number,
            'name': f'Pokémon #{reg.pokemon_number:03d}',
            'image': '',
            'types': ['normal'],
        }
        if query:
            match_name = query in pkmn.get('name', '').lower()
            match_num = query in str(reg.pokemon_number)
            match_nick = query in reg.nickname.lower()
            match_type = any(query in t.lower() for t in pkmn.get('types', []))
            if not (match_name or match_num or match_nick or match_type):
                continue

        items.append({
            'registration': reg,
            'pokemon': pkmn,
        })

    return render(
        request,
        'trainers/pokedex.html',
        {
            'active_trainer': active_trainer,
            'items': items,
            'total_registered': active_trainer.pokedex_registrations.count(),
            'form': form,
            'query': query,
            'only_favorite': only_favorite,
            'all_pokemon_names': get_all_pokemon_names(),
        },
    )


@login_required
def pokedex_update(request, registration_id):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    registration = get_object_or_404(active_trainer.pokedex_registrations, id=registration_id)
    pokemon = find_pokemon_by_number(registration.pokemon_number) or {
        'number': registration.pokemon_number,
        'name': f'Pokémon #{registration.pokemon_number:03d}',
        'image': '',
        'types': ['normal'],
    }

    if request.method == 'POST':
        form = PokedexRegistrationUpdateForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            return redirect('trainers:pokedex')
    else:
        form = PokedexRegistrationUpdateForm(instance=registration)

    return render(
        request,
        'trainers/pokedex_form.html',
        {
            'active_trainer': active_trainer,
            'registration': registration,
            'pokemon': pokemon,
            'form': form,
        },
    )


@login_required
@require_http_methods(['DELETE', 'POST'])
def pokedex_delete(request, registration_id):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return JsonResponse({'error': 'Personagem ativo não encontrado.'}, status=403)

    registration = get_object_or_404(active_trainer.pokedex_registrations, id=registration_id)
    registration.delete()

    if request.method == 'DELETE' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'deleted': True})
    return redirect('trainers:pokedex')


@login_required
def profile_detail(request):
    active_trainer = _get_active_trainer(request)
    if active_trainer is None:
        return redirect('trainers:profile_create')

    return render(
        request,
        'trainers/profile_page.html',
        {
            'active_trainer': active_trainer,
            'trainer_card': active_trainer.get_or_create_card(),
            'trainer_profiles': request.user.trainer_profiles.all(),
            'profile_form': TrainerProfileUpdateForm(instance=active_trainer),
            'password_form': PasswordChangeForm(request.user),
        },
    )
