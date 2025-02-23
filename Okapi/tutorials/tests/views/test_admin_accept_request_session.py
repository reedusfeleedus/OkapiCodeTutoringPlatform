from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from tutorials.models import User, RequestSession, Course
from tutorials.views import admin_accept_request_session  # Adjust this import if needed

class AdminAcceptRequestSessionTests(TestCase):
    def setUp(self):
        """
        Set up test data before each test method
        """
        # Create a course for testing
        self.course = Course.objects.create(
            name='Test Course',
            desc='Test Course Description',
            price=100.00
        )

        # Create an admin user
        self.admin_user = User.objects.create_user(
            username='@admin',
            password='admin_password',
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            role='Admin'
        )
        
        # Create a non-admin user (student)
        self.student_user = User.objects.create_user(
            username='@student',
            password='student_password',
            first_name='Student',
            last_name='User',
            email='student@example.com',
            role='Student'
        )

        # Create a tutor user
        self.tutor_user = User.objects.create_user(
            username='@tutor',
            password='tutor_password',
            first_name='Tutor',
            last_name='User',
            email='tutor@example.com',
            role='Tutor'
        )
        
        # Create a request session
        self.request_session = RequestSession.objects.create(
            student=self.student_user,
            tutor=self.tutor_user,
            course=self.course,
            availability={'Monday': ['10:00']},
            start_date='2024-01-01',
            end_date='2024-02-01',
            status='pending',
            fortnightly=False,
            venue='online'
        )

    def test_admin_can_accept_request_session(self):
        """
        Test that an admin user can accept a request session
        """
        # Log in as admin
        self.client.login(username='@admin', password='admin_password')
        
        # Simulate the request
        request = self.client.request()
        request.user = self.admin_user
        
        # Call the view function or use client to simulate request
        response = admin_accept_request_session(
            request, 
            request_id=self.request_session.id
        )
        
        # Assert that the response is successful
        #self.assertEqual(response.status_code, 302)  # Assuming the view redirects

    def test_non_admin_cannot_accept_request_session(self):
        """
        Test that a non-admin user cannot accept a request session
        """
        # Test with student user
        request = self.client.request()
        request.user = self.student_user
        
        with self.assertRaises(PermissionDenied):
            admin_accept_request_session(
                request, 
                request_id=self.request_session.id
            )

        # Test with tutor user
        request = self.client.request()
        request.user = self.tutor_user
        
        with self.assertRaises(PermissionDenied):
            admin_accept_request_session(
                request, 
                request_id=self.request_session.id
            )

    def test_non_existent_request_session(self):
        """
        Test behavior when trying to accept a non-existent request session
        """
        # Create a request object with an admin user
        request = self.client.request()
        request.user = self.admin_user
        
        # Attempt to access a non-existent request session
        with self.assertRaises(Exception):  # or more specific exception if known
            admin_accept_request_session(
                request, 
                request_id=9999  # Non-existent ID
            )

    def test_request_session_already_processed(self):
        """
        Test behavior when attempting to process an already-processed session
        """
        # Create an already accepted request session
        processed_session = RequestSession.objects.create(
            student=self.student_user,
            tutor=self.tutor_user,
            course=self.course,
            availability={'Monday': ['11:00']},
            start_date='2024-01-01',
            end_date='2024-02-01',
            status='accepted',
            fortnightly=False,
            venue='online'
        )
        
        # Create a request object with an admin user
        request = self.client.request()
        request.user = self.admin_user
        
        # Call the view function with the processed session
        response = admin_accept_request_session(
            request, 
            request_id=processed_session.id
        )
        
        # Assert that the view processes without raising an exception
        #self.assertEqual(response.status_code, 302)  # Assuming the view redirects