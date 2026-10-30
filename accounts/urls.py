from django.urls import path

from .views import TrainerLoginView, TrainerLogoutView, admin_user_delete, admin_users, signup

app_name = 'accounts'

urlpatterns = [
    path('entrar/', TrainerLoginView.as_view(), name='login'),
    path('sair/', TrainerLogoutView.as_view(), name='logout'),
    path('cadastro/', signup, name='signup'),
    path('admin/usuarios/', admin_users, name='admin_users'),
    path('admin/usuarios/<int:user_id>/excluir/', admin_user_delete, name='admin_user_delete'),
]
