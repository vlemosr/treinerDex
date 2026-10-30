from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import TrainerDexUserCreationForm, UsernameOrEmailAuthenticationForm


ADMIN_SESSION_KEY = 'trainerdex_admin_access'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'


class TrainerLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = UsernameOrEmailAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.session.get(ADMIN_SESSION_KEY):
            return redirect('accounts:admin_users')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session[ADMIN_SESSION_KEY] = True
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)
            return redirect('accounts:admin_users')

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
        return response


class TrainerLogoutView(LogoutView):
    pass


def _admin_has_access(request):
    return request.session.get(ADMIN_SESSION_KEY) is True


def admin_users(request):
    if not _admin_has_access(request):
        return redirect('accounts:login')

    users = User.objects.prefetch_related('trainer_profiles').order_by('-date_joined')
    return render(
        request,
        'accounts/admin_users.html',
        {
            'users': users,
            'users_count': users.count(),
        },
    )


@require_POST
def admin_user_delete(request, user_id):
    if not _admin_has_access(request):
        return redirect('accounts:login')

    user = User.objects.filter(id=user_id).first()
    if user:
        username = user.username
        user.delete()
        messages.success(request, f'Usuario {username} excluido com sucesso.')

    return redirect('accounts:admin_users')


def signup(request):
    if request.user.is_authenticated:
        return redirect('trainers:dashboard')

    if request.method == 'POST':
        form = TrainerDexUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('trainers:profile_create')
    else:
        form = TrainerDexUserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})
