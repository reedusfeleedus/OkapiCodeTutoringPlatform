from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tutorials.models import User, Course, RequestSession
from datetime import timedelta

class DashboardTests(TestCase):
    def setUp(self):
        """Set up test data before each test method"""
        # Create users
        self.admin = User.objects.create_user(
            username='@admin',
            password='admin123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            role='Admin'
        )
        
        self.student = User.objects.create_user(
            username='@student',
            password='student123',
            first_name='Student',
            last_name='User',
            email='student@test.com',
            role='Student'
        )
        
        self.tutor = User.objects.create_user(
            username='@tutor',
            password='tutor123',
            first_name='Tutor',
            last_name='User',
            email='tutor@test.com',
            role='Tutor'
        )

        # Create a course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=100.00
        )

        # Create request sessions
        today = timezone.now().date()
        self.future_session1 = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=30),
            availability={'monday': '09:00'}
        )
        
        self.future_session2 = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=today + timedelta(days=2),
            end_date=today + timedelta(days=30),
            availability={'tuesday': '10:00'}
        )

        self.pending_session = RequestSession.objects.create(
            student=self.student,
            course=self.course,
            status='pending',
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=30),
            availability={'wednesday': '11:00'}
        )

    def test_admin_dashboard(self):
        """Test admin dashboard view"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_dashboard.html')
        
        # Check context data
        self.assertEqual(response.context['students_count'], 1)
        self.assertEqual(response.context['tutors_count'], 1)
        self.assertEqual(response.context['admin_count'], 1)
        self.assertEqual(response.context['request_count'], 1)
        self.assertEqual(response.context['user'], self.admin)

    def test_student_dashboard(self):
        """Test student dashboard view"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        
        # Check context data
        self.assertEqual(response.context['next_session'], self.future_session1)
        self.assertEqual(list(response.context['upcoming_sessions']), [self.future_session2])
        self.assertEqual(list(response.context['courses']), [self.course])
        self.assertEqual(response.context['user'], self.student)

    def test_tutor_dashboard(self):
        """Test tutor dashboard view"""
        self.client.login(username='@tutor', password='tutor123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        
        # Check context data
        self.assertEqual(response.context['next_session'], self.future_session1)
        self.assertEqual(list(response.context['upcoming_sessions']), [self.future_session2])
        self.assertEqual(response.context['user'], self.tutor)

    def test_student_no_sessions(self):
        """Test student dashboard with no sessions"""
        # Create new student with no sessions
        new_student = User.objects.create_user(
            username='@student2',
            password='student123',
            first_name='Student2',
            last_name='User',
            email='student2@test.com',
            role='Student'
        )
        
        self.client.login(username='@student2', password='student123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['next_session'])
        self.assertEqual(len(response.context['upcoming_sessions']), 0)

    def test_tutor_no_sessions(self):
        """Test tutor dashboard with no sessions"""
        # Create new tutor with no sessions
        new_tutor = User.objects.create_user(
            username='@tutor2',
            password='tutor123',
            first_name='Tutor2',
            last_name='User',
            email='tutor2@test.com',
            role='Tutor'
        )
        
        self.client.login(username='@tutor2', password='tutor123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['next_session'])
        self.assertEqual(len(response.context['upcoming_sessions']), 0)

    def test_past_sessions_not_shown(self):
        """Test that past sessions are not shown in dashboards"""
        today = timezone.now().date()
        past_session = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=today - timedelta(days=1),
            end_date=today - timedelta(days=1),
            availability={'thursday': '12:00'}
        )
        
        # Check student dashboard
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('dashboard'))
        self.assertNotIn(past_session, response.context['upcoming_sessions'])
        
        # Check tutor dashboard
        self.client.login(username='@tutor', password='tutor123')
        response = self.client.get(reverse('dashboard'))
        self.assertNotIn(past_session, response.context['upcoming_sessions'])

    def test_pending_sessions_not_shown(self):
        """Test that pending sessions are not shown in upcoming sessions"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertNotIn(self.pending_session, response.context['upcoming_sessions'])
        self.assertNotEqual(response.context['next_session'], self.pending_session)

    def test_unauthenticated_access(self):
        """Test access to dashboard when not logged in"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login