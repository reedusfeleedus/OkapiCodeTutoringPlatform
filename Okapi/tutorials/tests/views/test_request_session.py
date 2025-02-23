from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.messages import get_messages
from tutorials.models import User, Course, RequestSession
from datetime import date

class RequestSessionTests(TestCase):
    def setUp(self):
        """Set up test data before each test method"""
        # Create a course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=100.00
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
        
        # Create a tutor user (for permission testing)
        self.tutor = User.objects.create_user(
            username='@tutor',
            password='tutor123',
            first_name='Tutor',
            last_name='User',
            email='tutor@test.com',
            role='Tutor'
        )

        # Base valid form data - now with single times instead of lists
        self.valid_form_data = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'cb_monday': 'on',
            'monday_time': '09:00',
            'cb_wednesday': 'on',
            'wednesday_time': '14:00'
        }

    def test_student_can_access_request_form(self):
        """Test that a student can access the request session form"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('request_session', args=[self.course.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sessions/request_session.html')
        self.assertIn('course', response.context)
        self.assertIn('weekdays', response.context)

    def test_non_student_cannot_access(self):
        """Test that non-students cannot access the request form"""
        self.client.login(username='@tutor', password='tutor123')
        response = self.client.get(reverse('request_session', args=[self.course.id]))
        self.assertEqual(response.status_code, 403)  # Should return 403 Forbidden

    def test_successful_request_creation(self):
        """Test successful creation of a request session"""
        self.client.login(username='@student', password='student123')
        
        response = self.client.post(
            reverse('request_session', args=[self.course.id]),
            data=self.valid_form_data
        )

        # Check if request session was created
        self.assertTrue(RequestSession.objects.exists())
        request_session = RequestSession.objects.first()
        
        # Verify request session details
        self.assertEqual(request_session.student, self.student)
        self.assertEqual(request_session.course, self.course)
        self.assertEqual(request_session.start_date.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(request_session.end_date.strftime('%Y-%m-%d'), '2024-01-31')
        
        # Check availability format matches implementation
        expected_availability = {
            'monday': '09:00',
            'wednesday': '14:00'
        }
        self.assertEqual(request_session.availability, expected_availability)
        
        # Check redirect
        self.assertRedirects(response, reverse('student.requests_list'))

    def test_missing_dates_validation(self):
        """Test validation when dates are missing"""
        self.client.login(username='@student', password='student123')
        
        # Remove dates from valid form data
        invalid_data = self.valid_form_data.copy()
        invalid_data.pop('start_date')
        invalid_data.pop('end_date')
        
        response = self.client.post(
            reverse('request_session', args=[self.course.id]),
            data=invalid_data
        )

        # Check that no request session was created
        self.assertFalse(RequestSession.objects.exists())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Start date and end date are required.", 
                     [str(m) for m in messages])

    def test_missing_availability_validation(self):
        """Test validation when no availability is selected"""
        self.client.login(username='@student', password='student123')
        
        # Only include dates, no availability
        invalid_data = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        response = self.client.post(
            reverse('request_session', args=[self.course.id]),
            data=invalid_data
        )

        # Check that no request session was created
        self.assertFalse(RequestSession.objects.exists())
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("You must select at least one day with an available time.", 
                     [str(m) for m in messages])

    def test_multiple_days_availability(self):
        """Test creating a request with multiple days and times"""
        self.client.login(username='@student', password='student123')
        
        multi_day_data = self.valid_form_data.copy()
        multi_day_data.update({
            'cb_friday': 'on',
            'friday_time': '16:00',
            'cb_saturday': 'on',
            'saturday_time': '10:00'
        })
        
        response = self.client.post(
            reverse('request_session', args=[self.course.id]),
            data=multi_day_data
        )

        request_session = RequestSession.objects.first()
        expected_availability = {
            'monday': '09:00',
            'wednesday': '14:00',
            'friday': '16:00',
            'saturday': '10:00'
        }
        self.assertEqual(request_session.availability, expected_availability)

    def test_invalid_course_id(self):
        """Test handling of invalid course ID"""
        self.client.login(username='@student', password='student123')
        
        response = self.client.get(
            reverse('request_session', args=[999])  # Non-existent course ID
        )
        
        self.assertEqual(response.status_code, 404)