from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from tutorials.models import User, Course
from tutorials.forms import CourseForm
from decimal import Decimal

class EditCourseTests(TestCase):
    def setUp(self):
        # Create an admin user
        self.admin = User.objects.create_user(
            username='@admin',
            password='admin123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            role='Admin'
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

        # Create a student
        self.student = User.objects.create_user(
            username='@student',
            password='student123',
            first_name='Student',
            last_name='User',
            email='student@test.com',
            role='Student'
        )

        # Create a test course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=Decimal('99.99')
        )
        self.course.users.add(self.tutor)

    def test_admin_can_access_edit_form(self):
        """Test that admin can access the course edit form"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('course.edit', args=[self.course.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/edit_course.html')
        self.assertIsInstance(response.context['form'], CourseForm)
        self.assertEqual(response.context['course'], self.course)

    def test_non_admin_cannot_access_edit_form(self):
        """Test that non-admin users cannot access the edit form"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('course.edit', args=[self.course.id]))
        self.assertEqual(response.status_code, 403)

    def test_successful_course_edit(self):
        """Test successful editing of a course"""
        self.client.login(username='@admin', password='admin123')
        
        updated_data = {
            'name': 'Advanced Python',
            'desc': 'Advanced Python concepts',
            'price': '149.99',
            'users': [self.tutor.id]
        }
        
        response = self.client.post(
            reverse('course.edit', args=[self.course.id]),
            data=updated_data
        )
        
        # Verify redirect on success
        self.assertRedirects(response, reverse('course_list'))
        
        # Refresh course from database
        self.course.refresh_from_db()
        
        # Verify course details were updated
        self.assertEqual(self.course.name, 'Advanced Python')
        self.assertEqual(self.course.desc, 'Advanced Python concepts')
        self.assertEqual(self.course.price, Decimal('149.99'))
        self.assertIn(self.tutor, self.course.users.all())

    def test_invalid_form_submission(self):
        """Test form submission with invalid data"""
        self.client.login(username='@admin', password='admin123')
        
        # Store original values
        original_name = self.course.name
        original_desc = self.course.desc
        original_price = self.course.price
        
        invalid_data = {
            'name': '',
            'desc': '',
            'price': '',
            'users': []
        }
        
        response = self.client.post(
            reverse('course.edit', args=[self.course.id]),
            data=invalid_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Verify course wasn't changed
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, original_name)
        self.assertEqual(self.course.desc, original_desc)
        self.assertEqual(self.course.price, original_price)

    def test_nonexistent_course(self):
        """Test editing a non-existent course"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('course.edit', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_edit_course_remove_all_tutors(self):
        """Test editing a course with no tutors"""
        self.client.login(username='@admin', password='admin123')
        
        # Try to update course with no tutors
        updated_data = {
            'name': 'Updated Course',
            'desc': 'Updated description',
            'price': '199.99',
            'users': []
        }
        
        response = self.client.post(
            reverse('course.edit', args=[self.course.id]),
            data=updated_data
        )
        
        # Verify the course wasn't updated
        self.assertEqual(response.status_code, 200)
        
        # Verify original data remains unchanged
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Python Programming')
        self.assertEqual(self.course.users.count(), 1)
        self.assertIn(self.tutor, self.course.users.all())

    def test_partial_update_preserves_other_fields(self):
        """Test that updating only some fields preserves others"""
        self.client.login(username='@admin', password='admin123')
        
        # Update only the name
        response = self.client.post(
            reverse('course.edit', args=[self.course.id]),
            data={
                'name': 'New Name',
                'desc': self.course.desc,
                'price': self.course.price,
                'users': [self.tutor.id]
            }
        )
        
        # Verify redirect on success
        self.assertRedirects(response, reverse('course_list'))
        
        # Refresh course from database
        self.course.refresh_from_db()
        
        # Verify only name changed
        self.assertEqual(self.course.name, 'New Name')
        self.assertEqual(self.course.desc, 'Learn Python basics')
        self.assertEqual(self.course.price, Decimal('99.99'))
        self.assertIn(self.tutor, self.course.users.all())