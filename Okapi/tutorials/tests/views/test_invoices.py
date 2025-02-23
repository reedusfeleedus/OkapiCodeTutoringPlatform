from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tutorials.models import User, Course, Invoices
from decimal import Decimal
from datetime import timedelta

class InvoicesViewTests(TestCase):
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

        # Create test invoices with different due dates
        self.paid_invoice1 = Invoices.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            due_date=timezone.now().date() + timedelta(days=1),
            payment_date=timezone.now().date(),
            status=True,
            total=Decimal('100.00')
        )

        self.paid_invoice2 = Invoices.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            due_date=timezone.now().date() + timedelta(days=2),
            payment_date=timezone.now().date(),
            status=True,
            total=Decimal('150.00')
        )

        self.unpaid_invoice1 = Invoices.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            due_date=timezone.now().date() + timedelta(days=3),
            status=False,
            total=Decimal('200.00')
        )

        self.unpaid_invoice2 = Invoices.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            due_date=timezone.now().date() + timedelta(days=4),
            status=False,
            total=Decimal('250.00')
        )

    def test_admin_can_view_all_invoices(self):
        """Test that admin can view all invoices"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('invoices'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices.html')
        
        # Admin should see all invoices
        self.assertEqual(len(response.context['paid_invoices']), 2)
        self.assertEqual(len(response.context['unpaid_invoices']), 2)

    def test_student_can_view_own_invoices(self):
        """Test that student can view only their invoices"""
        self.client.login(username='@student', password='student123')
        response = self.client.get(reverse('invoices'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verify student sees only their invoices
        paid_invoices = response.context['paid_invoices']
        unpaid_invoices = response.context['unpaid_invoices']
        
        self.assertEqual(len(paid_invoices), 2)
        self.assertEqual(len(unpaid_invoices), 2)
        
        # Verify all invoices belong to the student
        for invoice in paid_invoices:
            self.assertEqual(invoice.student, self.student)
        for invoice in unpaid_invoices:
            self.assertEqual(invoice.student, self.student)

    def test_tutor_can_view_own_invoices(self):
        """Test that tutor can view only their invoices"""
        self.client.login(username='@tutor', password='tutor123')
        response = self.client.get(reverse('invoices'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verify tutor sees only their invoices
        paid_invoices = response.context['paid_invoices']
        unpaid_invoices = response.context['unpaid_invoices']
        
        self.assertEqual(len(paid_invoices), 2)
        self.assertEqual(len(unpaid_invoices), 2)
        
        # Verify all invoices belong to the tutor
        for invoice in paid_invoices:
            self.assertEqual(invoice.tutor, self.tutor)
        for invoice in unpaid_invoices:
            self.assertEqual(invoice.tutor, self.tutor)

    def test_invoices_ordered_by_due_date(self):
        """Test that invoices are ordered by due date"""
        self.client.login(username='@admin', password='admin123')
        response = self.client.get(reverse('invoices'))
        
        paid_invoices = response.context['paid_invoices']
        unpaid_invoices = response.context['unpaid_invoices']
        
        # Check that invoices are ordered by due date
        self.assertTrue(all(paid_invoices[i].due_date <= paid_invoices[i+1].due_date 
                          for i in range(len(paid_invoices)-1)))
        self.assertTrue(all(unpaid_invoices[i].due_date <= unpaid_invoices[i+1].due_date 
                          for i in range(len(unpaid_invoices)-1)))

    def test_user_with_no_invoices(self):
        """Test view for user with no invoices"""
        # Create new student with no invoices
        new_student = User.objects.create_user(
            username='@student2',
            password='student123',
            first_name='Student2',
            last_name='User',
            email='student2@test.com',
            role='Student'
        )
        
        self.client.login(username='@student2', password='student123')
        response = self.client.get(reverse('invoices'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['paid_invoices']), 0)
        self.assertEqual(len(response.context['unpaid_invoices']), 0)

    def test_invalid_role_user(self):
        """Test view for user with invalid role"""
        invalid_user = User.objects.create_user(
            username='@invalid',
            password='invalid123',
            first_name='Invalid',
            last_name='User',
            email='invalid@test.com',
            role='Invalid'
        )
        
        self.client.login(username='@invalid', password='invalid123')
        response = self.client.get(reverse('invoices'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['paid_invoices']), 0)
        self.assertEqual(len(response.context['unpaid_invoices']), 0)

    
    