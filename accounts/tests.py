from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from trainers.models import TrainerProfile


class AccountFlowTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse('accounts:signup'),
            {
                'username': 'ash',
                'email': 'ash@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('trainers:profile_create'))
        self.assertTrue(User.objects.filter(username='ash').exists())
        self.assertFalse(TrainerProfile.objects.filter(user__username='ash').exists())

    def test_signup_does_not_require_email(self):
        response = self.client.post(
            reverse('accounts:signup'),
            {
                'username': 'gary',
                'email': '',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('trainers:profile_create'))
        self.assertEqual(User.objects.get(username='gary').email, '')

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username='misty',
            email='misty@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('accounts:signup'),
            {
                'username': 'misty2',
                'email': 'misty@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este e-mail ja esta em uso.')

    def test_signup_form_does_not_request_character_data(self):
        response = self.client.get(reverse('accounts:signup'))

        self.assertNotContains(response, 'name="city"')
        self.assertNotContains(response, 'name="gender"')

    def test_login_accepts_email(self):
        User.objects.create_user(
            username='sabrina',
            email='sabrina@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': 'sabrina@example.com',
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('trainers:dashboard'))
