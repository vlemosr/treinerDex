from django.contrib import admin

from .models import Friend, InventoryItem, Mission, MissionCompletion, PokedexRegistration, TrainerCard, TrainerProfile


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ('trainer_name', 'user', 'level', 'clan', 'city')
    search_fields = ('trainer_name', 'user__username', 'city')
    list_filter = ('clan', 'level')


@admin.register(PokedexRegistration)
class PokedexRegistrationAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'pokemon_number', 'registered_at')
    search_fields = ('trainer__trainer_name', 'pokemon_number')


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ('name', 'trainer', 'status', 'contact', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'contact', 'trainer__trainer_name')


@admin.register(MissionCompletion)
class MissionCompletionAdmin(admin.ModelAdmin):
    list_display = ('mission_key', 'trainer', 'xp_reward', 'completed_at')
    list_filter = ('mission_key',)
    search_fields = ('mission_key', 'trainer__trainer_name')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'trainer', 'slot_number', 'quantity')
    list_filter = ('slot_number',)
    search_fields = ('name', 'trainer__trainer_name')


@admin.register(TrainerCard)
class TrainerCardAdmin(admin.ModelAdmin):
    list_display = ('license_code', 'trainer', 'region', 'badges_count', 'issued_at')
    search_fields = ('license_code', 'trainer__trainer_name', 'region')


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'key', 'xp_reward')
    search_fields = ('title', 'key')
