from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

class TrainerDexUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, label='E-mail')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'Nome de usuario',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            return ''
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail ja esta em uso.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Usuario ou e-mail')

    def clean(self):
        login_identifier = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if login_identifier and password:
            username = login_identifier
            if '@' in login_identifier:
                user = User.objects.filter(email__iexact=login_identifier).first()
                username = user.get_username() if user else login_identifier

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
