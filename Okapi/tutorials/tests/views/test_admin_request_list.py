from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from tutorials.models import User, Course, RequestSession
from datetime import date

class AdminRequestListTests(TestCase):
    def setUp(self):
        """Set up test data before each test method"""
        # Create a course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=100.00
        )

        # Create an admin user
        self.admin = User.objects.create_user(
            username='@admin',
            password='admin123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            role='Admin'
        )

        # Create a student user
        self.student = User.objects.create_user(
            username='@student',
            password='student123',
            first_name='Student',
            last_name='User',
            email='student@test.com',
            role='Student'
        )

        # Create some request sessions
        self.request1 = RequestSession.objects.create(
            student=self.student,
            course=self.course,
            start_date='2024-01-01',
            end_date='2024-01-31',
            availability={'monday': '09:00'},
            status='pending'
        )

        self.request2 = RequestSession.objects.create(
            student=self.student,
            course=self.course,
            start_date='2024-02-01',
            end_date='2024-02-28',
            availability={'tuesday': '10:00'},
            status='pending'
        )

    def test_admin_can_access_list(self):
        """Test that admin can access the request list"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('admin.request.list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/sessions/requests.html')

    def test_non_admin_cannot_access_list(self):
        """Test that non-admin users cannot access the request list"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('admin.request.list'))
        self.assertEqual(response.status_code, 403)

    def test_requests_are_ordered_by_id_desc(self):
        """Test that requests are ordered by ID in descending order"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('admin.request.list'))
        
        requests = response.context['requests']
        self.assertEqual(list(requests), [self.request2, self.request1])

    def test_context_contains_all_requests(self):
        """Test that all requests are included in the context"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('admin.request.list'))
        
        requests = response.context['requests']
        self.assertEqual(requests.count(), 2)
        self.assertIn(self.request1, requests)
        self.assertIn(self.request2, requests)

    def test_unauthenticated_user_redirect(self):
        """Test that unauthenticated users are redirected"""
        # Get the admin request list URL
        admin_url = reverse('admin.request.list')
        
        # Try to access without login
        response = self.client.get(admin_url)
        
        # Check that it's a redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify redirect contains the next parameter with the original URL
        self.assertIn('next=', response.url)
        self.assertIn(admin_url, response.url)

    def test_empty_request_list(self):
        """Test displaying an empty request list"""
        # Delete all existing requests
        RequestSession.objects.all().delete()
        
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('admin.request.list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['requests']), 0)

    def test_multiple_requests_pagination(self):
        """Test that multiple requests are handled correctly"""
        # Create several more requests
        for i in range(3, 6):
            RequestSession.objects.create(
                student=self.student,
                course=self.course,
                start_date=f'2024-0{i}-01',
                end_date=f'2024-0{i}-28',
                availability={f'day{i}': f'{i+8}:00'},
                status='pending'
            )
        
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('admin.request.list'))
        
        # Verify all requests are present and in correct order
        requests = response.context['requests']
        self.assertEqual(requests.count(), 5)  # 2 original + 3 new
        self.assertEqual(requests.first(), RequestSession.objects.latest('id'))