from django.urls import path

from .views import (
    dashboard,
    friend_delete,
    friend_invite,
    friends_page,
    inventory_item_delete,
    mission_complete,
    password_update,
    pokedex_register,
    pokedex_search,
    profile_create,
    profile_delete,
    profile_select,
    profile_update,
    team_member_update,
)

app_name = 'trainers'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('treinador/criar/', profile_create, name='profile_create'),
    path('treinador/<int:profile_id>/selecionar/', profile_select, name='profile_select'),
    path('treinador/<int:profile_id>/excluir/', profile_delete, name='profile_delete'),
    path('treinador/editar/', profile_update, name='profile_update'),
    path('treinador/senha/', password_update, name='password_update'),
    path('treinador/equipe/atualizar/', team_member_update, name='team_member_update'),
    path('inventario/item/<int:item_id>/excluir/', inventory_item_delete, name='inventory_item_delete'),
    path('amigos/', friends_page, name='friends'),
    path('amigos/<int:friend_id>/convidar/', friend_invite, name='friend_invite'),
    path('amigos/<int:friend_id>/excluir/', friend_delete, name='friend_delete'),
    path('missoes/<slug:mission_key>/concluir/', mission_complete, name='mission_complete'),
    path('pokedex/buscar/', pokedex_search, name='pokedex_search'),
    path('pokedex/registrar/', pokedex_register, name='pokedex_register'),
    path('pokedex_register/', pokedex_register, name='pokedex_register_alias'),
]
