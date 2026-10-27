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

    def test_orders_view(self):
        self.client.login(username='client_test', password='TestPassword@123')
        response = self.client.get(reverse('portal:orders'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BI-TEST-9901')


import json
import hashlib
import hmac
from portal.models import PaymentTransaction
from portal.services import (
    create_payment_transaction,
    verify_payment_callback,
    handle_payment_webhook,
    compute_signature,
    get_payment_credentials,
)


class PaymentVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='payment_buyer',
            email='paybuyer@apexcorp.com',
            password='TestPassword@123'
        )
        self.creds = get_payment_credentials()

    def create_order(self, order_num, amount):
        return Order.objects.create(
            user=self.user,
            order_number=order_num,
            customer_name="Test Buyer",
            phone="9876543210",
            email="paybuyer@apexcorp.com",
            delivery_address="APMC Yard",
            subtotal=amount / Decimal('1.05'),
            tax_amount=amount - (amount / Decimal('1.05')),
            total_amount=amount,
            payment_method="upi",
            payment_status="unpaid",
            status="pending"
        )

    def test_01_full_payment(self):
        order = self.create_order("ORD-TEST-001", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("100.00"), provider="razorpay")
        pay_id = "pay_001_full"
        sig = compute_signature(f"{txn.provider_order_id}|{pay_id}", self.creds['key_secret'])
        res = verify_payment_callback(order.order_number, txn.provider_order_id, pay_id, sig, Decimal("100.00"))
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.verified_paid_amount, Decimal("100.00"))
        self.assertEqual(order.outstanding_balance, Decimal("0.00"))

    def test_02_partial_payment(self):
        order = self.create_order("ORD-TEST-002", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("80.00"), provider="razorpay")
        pay_id = "pay_002_part"
        sig = compute_signature(f"{txn.provider_order_id}|{pay_id}", self.creds['key_secret'])
        res = verify_payment_callback(order.order_number, txn.provider_order_id, pay_id, sig, Decimal("80.00"))
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "partial")
        self.assertEqual(order.verified_paid_amount, Decimal("80.00"))
        self.assertEqual(order.outstanding_balance, Decimal("20.00"))

    def test_03_remaining_balance(self):
        order = self.create_order("ORD-TEST-003", Decimal("100.00"))
        txn1 = create_payment_transaction(order, Decimal("80.00"), provider="razorpay")
        sig1 = compute_signature(f"{txn1.provider_order_id}|pay_p1", self.creds['key_secret'])
        verify_payment_callback(order.order_number, txn1.provider_order_id, "pay_p1", sig1, Decimal("80.00"))

        txn2 = create_payment_transaction(order, order.outstanding_balance, provider="razorpay")
        sig2 = compute_signature(f"{txn2.provider_order_id}|pay_p2", self.creds['key_secret'])
        res2 = verify_payment_callback(order.order_number, txn2.provider_order_id, "pay_p2", sig2, Decimal("20.00"))
        order.refresh_from_db()
        self.assertTrue(res2['success'])
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.verified_paid_amount, Decimal("100.00"))
        self.assertEqual(order.outstanding_balance, Decimal("0.00"))

    def test_04_failed_payment(self):
        order = self.create_order("ORD-TEST-004", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("100.00"), provider="razorpay")
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_004_failed",
                        "order_id": txn.provider_order_id,
                        "amount": 10000,
                        "notes": {"order_number": order.order_number}
                    }
                }
            }
        }
        raw_bytes = json.dumps(payload).encode('utf-8')
        sig = hmac.new(self.creds['webhook_secret'].encode('utf-8'), raw_bytes, hashlib.sha256).hexdigest()
        res = handle_payment_webhook(raw_bytes, sig)
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "failed")
        self.assertEqual(order.verified_paid_amount, Decimal("0.00"))

    def test_05_delayed_webhook(self):
        order = self.create_order("ORD-TEST-005", Decimal("150.00"))
        txn = create_payment_transaction(order, Decimal("150.00"), provider="razorpay")
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_005_delayed",
                        "order_id": txn.provider_order_id,
                        "amount": 15000,
                        "currency": "INR",
                        "status": "captured",
                        "notes": {"order_number": order.order_number}
                    }
                }
            }
        }
        raw_bytes = json.dumps(payload).encode('utf-8')
        sig = hmac.new(self.creds['webhook_secret'].encode('utf-8'), raw_bytes, hashlib.sha256).hexdigest()
        res = handle_payment_webhook(raw_bytes, sig)
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.verified_paid_amount, Decimal("150.00"))

    def test_06_duplicate_callback_idempotency(self):
        order = self.create_order("ORD-TEST-006", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("100.00"), provider="razorpay")
        sig = compute_signature(f"{txn.provider_order_id}|pay_idem", self.creds['key_secret'])
        res1 = verify_payment_callback(order.order_number, txn.provider_order_id, "pay_idem", sig, Decimal("100.00"))
        self.assertTrue(res1['success'])
        res2 = verify_payment_callback(order.order_number, txn.provider_order_id, "pay_idem", sig, Decimal("100.00"))
        self.assertTrue(res2['success'])
        self.assertTrue(res2.get('duplicate'))
        order.refresh_from_db()
        self.assertEqual(order.verified_paid_amount, Decimal("100.00"))

    def test_07_invalid_signature_rejected(self):
        order = self.create_order("ORD-TEST-007", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("100.00"), provider="razorpay")
        res = verify_payment_callback(order.order_number, txn.provider_order_id, "pay_tamper", "invalid_sig", Decimal("100.00"))
        order.refresh_from_db()
        self.assertFalse(res['success'])
        self.assertEqual(order.payment_status, "unpaid")

    def test_08_order_mismatch_rejected(self):
        order_a = self.create_order("ORD-TEST-008A", Decimal("100.00"))
        order_b = self.create_order("ORD-TEST-008B", Decimal("100.00"))
        txn_b = create_payment_transaction(order_b, Decimal("100.00"), provider="razorpay")
        sig_b = compute_signature(f"{txn_b.provider_order_id}|pay_b", self.creds['key_secret'])
        res = verify_payment_callback(order_a.order_number, txn_b.provider_order_id, "pay_b", sig_b, Decimal("100.00"))
        self.assertFalse(res['success'])
        order_a.refresh_from_db()
        self.assertEqual(order_a.payment_status, "unpaid")

    def test_09_manipulated_amount_partial(self):
        order = self.create_order("ORD-TEST-009", Decimal("500.00"))
        txn = create_payment_transaction(order, Decimal("500.00"), provider="razorpay")
        sig = compute_signature(f"{txn.provider_order_id}|pay_manip", self.creds['key_secret'])
        res = verify_payment_callback(order.order_number, txn.provider_order_id, "pay_manip", sig, Decimal("1.00"))
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "partial")
        self.assertEqual(order.verified_paid_amount, Decimal("1.00"))
        self.assertEqual(order.outstanding_balance, Decimal("499.00"))

    def test_10_excess_payment_tracked(self):
        order = self.create_order("ORD-TEST-010", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("120.00"), provider="razorpay")
        sig = compute_signature(f"{txn.provider_order_id}|pay_excess", self.creds['key_secret'])
        res = verify_payment_callback(order.order_number, txn.provider_order_id, "pay_excess", sig, Decimal("120.00"))
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.verified_paid_amount, Decimal("120.00"))
        self.assertEqual(order.excess_amount, Decimal("20.00"))

    def test_11_rapid_refreshes(self):
        order = self.create_order("ORD-TEST-011", Decimal("250.00"))
        self.client.force_login(self.user)
        for _ in range(3):
            resp = self.client.post(f"/products/api/payment-create/{order.order_number}/", data=json.dumps({"provider": "razorpay"}), content_type="application/json")
            self.assertTrue(resp.json()["success"])
        for _ in range(3):
            resp = self.client.get(f"/products/api/order-status/{order.order_number}/")
            self.assertEqual(Decimal(str(resp.json()["outstanding_balance"])), Decimal("250.00"))

    def test_12_atomic_concurrency(self):
        order = self.create_order("ORD-TEST-012", Decimal("100.00"))
        txn = create_payment_transaction(order, Decimal("100.00"), provider="razorpay")
        sig = compute_signature(f"{txn.provider_order_id}|pay_conc", self.creds['key_secret'])
        res = verify_payment_callback(order.order_number, txn.provider_order_id, "pay_conc", sig, Decimal("100.00"))
        order.refresh_from_db()
        self.assertTrue(res['success'])
        self.assertEqual(order.payment_status, "paid")
