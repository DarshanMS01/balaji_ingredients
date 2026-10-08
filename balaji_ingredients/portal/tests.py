"""
portal/tests.py
Unit and integration tests for B2B Client Registration, Login, Dashboard, and Orders.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from portal.models import CompanyProfile, Order, OrderItem


class PortalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='client_test',
            email='test@apexcorp.com',
            password='TestPassword@123'
        )
        self.profile = CompanyProfile.objects.create(
            user=self.user,
            company_name='Apex Test Foods Ltd',
            gstin='29AAACT1234A1Z1',
            phone='+91 98888 77777',
            address_line1='Test Industrial Estate',
            city='Bengaluru',
            state='Karnataka',
            pincode='560001'
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number='BI-TEST-9901',
            status='dispatched',
            payment_status='advance_paid',
            subtotal=Decimal('500000.00'),
            tax_amount=Decimal('25000.00'),
            total_amount=Decimal('525000.00'),
            carrier_name='VRL Test Freight',
            tracking_consignment_no='LR-100234'
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product_name='Test Toor Dal',
            quantity=Decimal('5.00'),
            unit='Metric Tons',
            unit_price=Decimal('100000.00'),
            total_price=Decimal('500000.00')
        )

    def test_login_and_dashboard(self):
        login_success = self.client.login(username='client_test', password='TestPassword@123')
        self.assertTrue(login_success)

        response = self.client.get(reverse('portal:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apex Test Foods Ltd')
        self.assertContains(response, 'BI-TEST-9901')

    def test_order_detail_view(self):
        self.client.login(username='client_test', password='TestPassword@123')
        response = self.client.get(reverse('portal:order_detail', kwargs={'order_number': 'BI-TEST-9901'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VRL Test Freight')
        self.assertContains(response, 'LR-100234')
        self.assertContains(response, 'Test Toor Dal')

    def test_proforma_invoice_view(self):
        self.client.login(username='client_test', password='TestPassword@123')
        response = self.client.get(reverse('portal:invoice', kwargs={'order_number': 'BI-TEST-9901'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PROFORMA INVOICE')
        self.assertContains(response, '525,000.00')
