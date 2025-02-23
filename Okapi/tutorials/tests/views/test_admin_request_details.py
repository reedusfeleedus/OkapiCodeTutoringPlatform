from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from tutorials.models import User, RequestSession, Course, Invoices
from datetime import date, timedelta
import ast

class AdminRequestDetailsTests(TestCase):
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
            username='@adminuser',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            role='Admin'
        )
        
        # Create a student
        self.student = User.objects.create_user(
            username='@studentuser',
            password='studentpass123',
            first_name='Student',
            last_name='User',
            email='student@test.com',
            role='Student'
        )
        
        # Create a tutor
        self.tutor = User.objects.create_user(
            username='@tutoruser',
            password='tutorpass123',
            first_name='Tutor',
            last_name='User',
            email='tutor@test.com',
            role='Tutor'
        )

        # Add tutor to course
        self.course.users.add(self.tutor)
        
        # Create request session
        self.request_session = RequestSession.objects.create(
            student=self.student,
            course=self.course,
            availability={'monday': ['09:00', '10:00']},
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            status='pending',
            venue='online'
        )

    def test_non_admin_access_denied(self):
        """Test that non-admin users cannot access the view"""
        self.client.login(username='@studentuser', password='studentpass123')
        response = self.client.get(
            reverse('admin.request.details', args=[self.request_session.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_details(self):
        """Test that admin can view request session details"""
        self.client.login(username='@adminuser', password='adminpass123')
        response = self.client.get(
            reverse('admin.request.details', args=[self.request_session.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/sessions/request_details.html')
        self.assertIn('request_session', response.context)
        self.assertIn('tutors', response.context)

    def test_admin_can_assign_tutor_and_create_invoice(self):
        """Test that an admin can assign a tutor and create an invoice when accepting a session"""
        self.client.login(username='@adminuser', password='adminpass123')
        
        post_data = {
            'status': 'accepted',
            'tutor': self.tutor.id
        }
        
        response = self.client.post(
            reverse('admin.request.details', args=[self.request_session.id]),
            data=post_data
        )

        # Verify the request session was updated
        updated_session = RequestSession.objects.get(id=self.request_session.id)
        self.assertEqual(updated_session.status, 'accepted')
        self.assertEqual(updated_session.tutor, self.tutor)

        # Verify invoice was created
        invoice = Invoices.objects.filter(
            student=self.student,
            tutor=self.tutor,
            course=self.course
        ).first()
        
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.student, self.student)
        self.assertEqual(invoice.tutor, self.tutor)
        self.assertEqual(invoice.course, self.course)
        
        # Check due date is 3 days after start date
        expected_due_date = date(2024, 1, 4)  # Jan 1 + 3 days
        self.assertEqual(invoice.due_date, expected_due_date)

    def test_admin_can_reject_request(self):
        """Test that admin can reject a request session"""
        self.client.login(username='@adminuser', password='adminpass123')
        
        post_data = {
            'status': 'rejected'
        }
        
        response = self.client.post(
            reverse('admin.request.details', args=[self.request_session.id]),
            data=post_data
        )

        # Verify the request session was updated
        updated_session = RequestSession.objects.get(id=self.request_session.id)
        self.assertEqual(updated_session.status, 'rejected')
        
        # Verify no invoice was created
        invoice_exists = Invoices.objects.filter(
            student=self.student,
            course=self.course
        ).exists()
        self.assertFalse(invoice_exists)

    def test_invalid_request_status(self):
        """Test handling of invalid status values"""
        self.client.login(username='@adminuser', password='adminpass123')
        
        post_data = {
            'status': 'invalid_status'
        }
        
        response = self.client.post(
            reverse('admin.request.details', args=[self.request_session.id]),
            data=post_data
        )

        # Verify the request session status remains unchanged
        updated_session = RequestSession.objects.get(id=self.request_session.id)
        self.assertEqual(updated_session.status, 'pending')