from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Profile
from jobs.models import Skill


class ProfileSignalTests(TestCase):
    def test_profile_created_automatically(self):
        user = User.objects.create_user(username='newuser', password='testpass123')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_completeness_starts_low(self):
        user = User.objects.create_user(username='blankuser', password='testpass123')
        self.assertLess(user.profile.completeness, 50)

    def test_profile_completeness_increases(self):
        user = User.objects.create_user(username='fulluser', password='testpass123')
        profile = user.profile
        profile.headline = 'Software Engineer'
        profile.bio = 'I build things.'
        profile.desired_role = 'Backend Engineer'
        profile.desired_location = 'Remote'
        profile.expected_salary = 100000
        profile.linkedin_url = 'https://linkedin.com/in/example'
        profile.save()
        skill = Skill.objects.create(name='Python')
        profile.skills.add(skill)
        self.assertEqual(profile.completeness, 100)


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), {
            'role': 'seeker',
            'username': 'freshuser',
            'first_name': 'Fresh',
            'last_name': 'User',
            'email': 'fresh@example.com',
            'password1': 'SuperSecret123!',
            'password2': 'SuperSecret123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='freshuser').exists())
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_register_password_mismatch_fails(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'baduser',
            'email': 'bad@example.com',
            'password1': 'SuperSecret123!',
            'password2': 'DifferentPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='dashuser', password='testpass123')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_when_logged_in(self):
        self.client.login(username='dashuser', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_updates_data(self):
        self.client.login(username='dashuser', password='testpass123')
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Dash', 'last_name': 'User', 'email': 'dash@example.com',
            'headline': 'Aspiring Engineer', 'bio': '', 'desired_role': 'Software Engineer',
            'desired_location': 'Remote', 'experience_level': 'entry', 'open_to_remote': 'on',
            'expected_salary': '75000', 'linkedin_url': '', 'github_url': '', 'portfolio_url': '',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.headline, 'Aspiring Engineer')


class RoleBasedRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_as_seeker_goes_to_profile_edit(self):
        response = self.client.post(reverse('accounts:register'), {
            'role': 'seeker', 'username': 'seekeruser', 'email': 'seeker@example.com',
            'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        self.assertRedirects(response, reverse('accounts:profile_edit'))
        user = User.objects.get(username='seekeruser')
        self.assertEqual(user.profile.role, 'seeker')
        self.assertFalse(user.profile.is_employer)

    def test_register_as_employer_goes_to_company_setup(self):
        response = self.client.post(reverse('accounts:register'), {
            'role': 'employer', 'username': 'employeruser', 'email': 'employer@example.com',
            'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/employer/company/', response.url)
        user = User.objects.get(username='employeruser')
        self.assertTrue(user.profile.is_employer)

    def test_employer_dashboard_renders_for_employer_role(self):
        self.client.post(reverse('accounts:register'), {
            'role': 'employer', 'username': 'empdash', 'email': 'empdash@example.com',
            'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard_employer.html')

    def test_seeker_dashboard_uses_seeker_template(self):
        self.client.post(reverse('accounts:register'), {
            'role': 'seeker', 'username': 'seekdash', 'email': 'seekdash@example.com',
            'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard.html')


class PublicProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pubuser', password='testpass123')

    def test_private_profile_returns_404_for_others(self):
        response = self.client.get(reverse('accounts:public_profile', args=['pubuser']))
        self.assertEqual(response.status_code, 404)

    def test_private_profile_visible_to_owner(self):
        self.client.login(username='pubuser', password='testpass123')
        response = self.client.get(reverse('accounts:public_profile', args=['pubuser']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'private')

    def test_public_profile_visible_to_everyone(self):
        self.user.profile.is_public = True
        self.user.profile.save()
        response = self.client.get(reverse('accounts:public_profile', args=['pubuser']))
        self.assertEqual(response.status_code, 200)

    def test_unknown_username_404s(self):
        response = self.client.get(reverse('accounts:public_profile', args=['nosuchuser']))
        self.assertEqual(response.status_code, 404)
