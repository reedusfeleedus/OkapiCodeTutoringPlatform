"""Tests of the sign up view."""
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from tutorials.forms import SignUpForm
from tutorials.models import User
from tutorials.tests.helpers import LogInTester

class SignUpViewTestCase(TestCase, LogInTester):
    """Tests of the sign up view."""

    fixtures = ['tutorials/tests/fixtures/default_user.json']

    def setUp(self):
        self.url = reverse('sign_up')
        self.form_input = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'username': '@janedoe',
            'email': 'janedoe@example.org',
            'new_password': 'Password123',
            'password_confirmation': 'Password123'
        }
        self.user = User.objects.get(username='@johndoe')

    def test_sign_up_url(self):
        self.assertEqual(self.url,'/sign_up/')

    def test_get_sign_up(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertFalse(form.is_bound)

    def test_get_sign_up_redirects_when_logged_in(self):
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_unsuccesful_sign_up(self):
        self.form_input['username'] = 'BAD_USERNAME'
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertTrue(form.is_bound)
        self.assertFalse(self._is_logged_in())

    def test_succesful_sign_up(self):
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count+1)
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        user = User.objects.get(username='@janedoe')
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'janedoe@example.org')
        is_password_correct = check_password('Password123', user.password)
        self.assertTrue(is_password_correct)
        self.assertTrue(self._is_logged_in())

    def test_post_sign_up_redirects_when_logged_in(self):
        self.client.login(username=self.user.username, password="Password123")
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')


    from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tutorials.models import User, Course, RequestSession
from datetime import timedelta

class AllSessionsTests(TestCase):
    def setUp(self):
        """Set up test data before each test method"""
        # Create Course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=100.00
        )

        # Create users
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

        self.today = timezone.now().date()
        
        # Create past sessions
        self.past_session1 = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=self.today - timedelta(days=2),
            end_date=self.today - timedelta(days=1),
            availability={'monday': '09:00'}
        )

        self.past_session2 = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=self.today - timedelta(days=4),
            end_date=self.today - timedelta(days=3),
            availability={'tuesday': '10:00'}
        )

        # Create future sessions
        self.future_session1 = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            availability={'wednesday': '11:00'}
        )

        self.future_session2 = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='accepted',
            start_date=self.today + timedelta(days=3),
            end_date=self.today + timedelta(days=4),
            availability={'thursday': '12:00'}
        )

        # Create pending session (should not appear in lists)
        self.pending_session = RequestSession.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            status='pending',
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            availability={'friday': '13:00'}
        )

    def test_student_can_view_sessions(self):
        """Test that students can view their sessions correctly"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('all_sessions'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sessions.html')
        
        # Check context data
        self.assertEqual(response.context['next_session'], self.future_session1)
        self.assertEqual(list(response.context['upcoming_sessions']), [self.future_session2])
        self.assertEqual(list(response.context['previous_sessions']), 
                        [self.past_session2, self.past_session1])  # Ordered by start_date
        self.assertEqual(response.context['user'], self.student)

    def test_tutor_can_view_sessions(self):
        """Test that tutors can view their sessions correctly"""
        self.client.login(username='@tutor', password='tutor123')
        response = self.client.get(reverse('all_sessions'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sessions.html')
        
        # Check context data
        self.assertEqual(response.context['next_session'], self.future_session1)
        self.assertEqual(list(response.context['upcoming_sessions']), [self.future_session2])
        self.assertEqual(list(response.context['previous_sessions']), 
                        [self.past_session2, self.past_session1])
        self.assertEqual(response.context['user'], self.tutor)

    def test_student_with_no_sessions(self):
        """Test view for student with no sessions"""
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
        response = self.client.get(reverse('all_sessions'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['next_session'])
        self.assertEqual(len(response.context['upcoming_sessions']), 0)
        self.assertEqual(len(response.context['previous_sessions']), 0)

    def test_tutor_with_no_sessions(self):
        """Test view for tutor with no sessions"""
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
        response = self.client.get(reverse('all_sessions'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['next_session'])
        self.assertEqual(len(response.context['upcoming_sessions']), 0)
        self.assertEqual(len(response.context['previous_sessions']), 0)

    def test_pending_sessions_not_included(self):
        """Test that pending sessions are not included in the lists"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('all_sessions'))
        
        self.assertNotIn(self.pending_session, response.context['upcoming_sessions'])
        self.assertNotIn(self.pending_session, response.context['previous_sessions'])
        self.assertNotEqual(response.context['next_session'], self.pending_session)

    def test_session_date_ordering(self):
        """Test that sessions are correctly ordered by date"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('all_sessions'))
        
        previous_sessions = response.context['previous_sessions']
        upcoming_sessions = response.context['upcoming_sessions']
        
        # Check that previous sessions are in ascending order
        self.assertTrue(all(previous_sessions[i].start_date <= previous_sessions[i+1].start_date 
                          for i in range(len(previous_sessions)-1)))
        
        # Check that upcoming sessions are in ascending order
        self.assertTrue(all(upcoming_sessions[i].start_date <= upcoming_sessions[i+1].start_date 
                          for i in range(len(upcoming_sessions)-1)))

    def test_unauthenticated_access(self):
        """Test access attempt without login"""
        response = self.client.get(reverse('all_sessions'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
