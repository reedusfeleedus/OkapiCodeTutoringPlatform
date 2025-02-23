from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from tutorials.models import User

class ShowUsernamesTests(TestCase):
    def setUp(self):
        """Set up test data before each test method"""
        # Create an admin user
        self.admin = User.objects.create_user(
            username='@admin',
            password='admin123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            role='Admin'
        )

        # Create a student
        self.student = User.objects.create_user(
            username='@student',
            password='student123',
            first_name='Student',
            last_name='User',
            email='student@test.com',
            role='Student'
        )

        # Create a tutor
        self.tutor = User.objects.create_user(
            username='@tutor',
            password='tutor123',
            first_name='Tutor',
            last_name='User',
            email='tutor@test.com',
            role='Tutor'
        )

    def test_empty_users_list(self):
        """Test view behavior when no other users exist except admin"""
        # Login as admin first
        self.client.login(username='@admin', password='admin123')
        
        # Delete all users except admin
        User.objects.exclude(username='@admin').delete()
        
        response = self.client.get(reverse('show_usernames'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['usernames']), 1)
        self.assertEqual(response.context['usernames'], ['@admin'])

    def test_single_user_list(self):
        """Test view behavior when only admin exists"""
        # Login as admin
        self.client.login(username='@admin', password='admin123')
        
        # Delete other users
        User.objects.exclude(username='@admin').delete()
        
        response = self.client.get(reverse('show_usernames'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usernames_list.html')
        self.assertEqual(response.context['usernames'], ['@admin'])

    # ... rest of the test methods remain the same ...