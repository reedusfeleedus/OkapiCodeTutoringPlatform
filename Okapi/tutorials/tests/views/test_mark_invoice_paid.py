from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from tutorials.models import User, Course, Invoices
from decimal import Decimal

class MarkInvoicePaidTests(TestCase):
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

        # Create a course
        self.course = Course.objects.create(
            name='Python Programming',
            desc='Learn Python basics',
            price=Decimal('99.99')
        )

        # Create an unpaid invoice
        self.invoice = Invoices.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            due_date=timezone.now().date(),
            status=False,
            total=Decimal('99.99')
        )

    def test_admin_can_mark_invoice_paid(self):
        """Test that admin can successfully mark an invoice as paid"""
        self.client.login(username='@admin', password='admin123')
        
        response = self.client.post(reverse('mark_invoice_paid', args=[self.invoice.id]))
        
        # Refresh invoice from database
        self.invoice.refresh_from_db()
        
        # Check that invoice was marked as paid
        self.assertTrue(self.invoice.status)
        self.assertEqual(self.invoice.payment_date, timezone.now().date())
        
        # Check redirect
        self.assertRedirects(response, reverse('invoices'))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), f"Invoice for {self.course.name} has been marked as paid.")

    def test_non_admin_cannot_mark_invoice_paid(self):
        """Test that non-admin users cannot mark invoices as paid"""
        # Test with student
        self.client.login(username='@student', password='student123')
        response = self.client.post(reverse('mark_invoice_paid', args=[self.invoice.id]))
        
        # Refresh invoice from database
        self.invoice.refresh_from_db()
        
        # Check that invoice status hasn't changed
        self.assertFalse(self.invoice.status)
        self.assertIsNone(self.invoice.payment_date)
        
        # Check redirect
        self.assertRedirects(response, reverse('invoices'))
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "You do not have permission to mark invoices as paid.")

    def test_mark_nonexistent_invoice(self):
        """Test handling of non-existent invoice ID"""
        self.client.login(username='@admin', password='admin123')
        
        response = self.client.post(reverse('mark_invoice_paid', args=[999]))
        
        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_cannot_mark_already_paid_invoice(self):
        """Test handling of already paid invoice"""
        # First mark the invoice as paid
        self.invoice.status = True
        self.invoice.payment_date = timezone.now().date()
        self.invoice.save()

        self.client.login(username='@admin', password='admin123')
        original_payment_date = self.invoice.payment_date
        
        # Try to mark it as paid again
        response = self.client.post(reverse('mark_invoice_paid', args=[self.invoice.id]))
        
        # Refresh invoice from database
        self.invoice.refresh_from_db()
        
        # Payment date should not have changed
        self.assertEqual(self.invoice.payment_date, original_payment_date)

    def test_mark_multiple_invoices_paid(self):
        """Test marking multiple invoices as paid"""
        self.client.login(username='@admin', password='admin123')
        
        # Create second invoice
        invoice2 = Invoices.objects.create(
            student=self.student,
            tutor=self.tutor,
            course=self.course,
            due_date=timezone.now().date(),
            status=False,
            total=Decimal('149.99')
        )
        
        # Mark both invoices as paid
        for invoice in [self.invoice, invoice2]:
            response = self.client.post(reverse('mark_invoice_paid', args=[invoice.id]))
            invoice.refresh_from_db()
            self.assertTrue(invoice.status)
            self.assertEqual(invoice.payment_date, timezone.now().date())

    def test_payment_date_accuracy(self):
        """Test that payment date is set to current date"""
        self.client.login(username='@admin', password='admin123')
        today = timezone.now().date()
        
        response = self.client.post(reverse('mark_invoice_paid', args=[self.invoice.id]))
        
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.payment_date, today)

    def test_unauthenticated_user_redirect(self):
        """Test that unauthenticated users are redirected"""
        response = self.client.post(reverse('mark_invoice_paid', args=[self.invoice.id]))
        
        # Refresh invoice from database
        self.invoice.refresh_from_db()
        
        # Check that invoice status hasn't changed
        self.assertFalse(self.invoice.status)
        self.assertIsNone(self.invoice.payment_date)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)