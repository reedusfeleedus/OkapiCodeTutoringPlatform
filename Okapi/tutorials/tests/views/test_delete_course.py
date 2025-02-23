from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from tutorials.models import User, Course
from decimal import Decimal

class DeleteCourseTests(TestCase):
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

        # Create a non-admin user
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

        # Create a test course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=Decimal('99.99')
        )
        self.course.users.add(self.tutor)

    def test_admin_can_access_delete_page(self):
        """Test that admin can access the delete confirmation page"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('course.delete', args=[self.course.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/delete_course.html')
        self.assertEqual(response.context['course'], self.course)

    def test_non_admin_cannot_access_delete_page(self):
        """Test that non-admin users cannot access the delete page"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('course.delete', args=[self.course.id]))
        self.assertEqual(response.status_code, 403)

    def test_successful_course_deletion(self):
        """Test successful deletion of a course"""
        self.client.login(username='@admin', password='admin123')
        
        # Verify course exists before deletion
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())
        
        # Attempt to delete the course
        response = self.client.post(reverse('course.delete', args=[self.course.id]))
        
        # Verify redirect
        self.assertRedirects(response, reverse('course_list'))
        
        # Verify course was deleted
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_non_admin_cannot_delete_course(self):
        """Test that non-admin users cannot delete a course"""
        self.client.login(username='@student', password='student123')
        
        # Verify course exists before attempt
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())
        
        # Attempt to delete
        response = self.client.post(reverse('course.delete', args=[self.course.id]))
        
        # Verify permission denied
        self.assertEqual(response.status_code, 403)
        
        # Verify course still exists
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_get_request_does_not_delete(self):
        """Test that GET request doesn't delete the course"""
        self.client.login(username='@admin', password='admin123')
        
        # Send GET request
        response = self.client.get(reverse('course.delete', args=[self.course.id]))
        
        # Verify course still exists
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())
        
        # Verify template is shown
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/delete_course.html')

    def test_delete_nonexistent_course(self):
        """Test attempt to delete a non-existent course"""
        self.client.login(username='@admin', password='admin123')
        
        # Attempt to delete non-existent course
        with self.assertRaises(Course.DoesNotExist):
            response = self.client.post(reverse('course.delete', args=[999]))

    def test_delete_course_removes_tutor_association(self):
        """Test that deleting a course removes tutor associations"""
        self.client.login(username='@admin', password='admin123')
        
        # Store tutor's initial course count
        initial_course_count = self.tutor.courses.count()
        
        # Delete the course
        response = self.client.post(reverse('course.delete', args=[self.course.id]))
        
        # Verify tutor no longer has the course
        self.assertEqual(self.tutor.courses.count(), initial_course_count - 1)
        self.assertNotIn(self.course, self.tutor.courses.all())

    def test_unauthenticated_user_redirect(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(reverse('course.delete', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Verify redirect occurs
        
        # Don't check specific URL, just verify it's a redirect
        self.assertIsNotNone(response.url)


    def test_deletion_confirmation_get(self):
        """Test that GET request shows confirmation page with correct course"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('course.delete', args=[self.course.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/delete_course.html')
        self.assertEqual(response.context['course'].name, 'Python Programming')



    def test_delete_course_requires_login(self):
        """Test that delete course view requires authentication"""
        # Ensure user is logged out
        self.client.logout()
        
        # Try to delete course
        response = self.client.post(reverse('course.delete', args=[self.course.id]))
        
        # Verify redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify course still exists
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())