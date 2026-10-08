"""
products/tests.py
Unit and integration tests for Product Catalog, Specifications, and RFQ.
"""

from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, Product, ProductSpecification, QuoteRequest


class ProductCatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Dal & Pulses',
            slug='dal-pulses',
            description='Test category description',
            order=1
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Test Premium Toor Dal',
            slug='test-premium-toor-dal',
            subtitle='Test subtitle',
            description='Test long description',
            grade='Grade A Sortex',
            purity_percentage='99.7%',
            moisture_content='< 10%',
            origin='Karnataka'
        )
        self.spec = ProductSpecification.objects.create(
            product=self.product,
            parameter_name='Optical Purity',
            parameter_value='99.7% Min',
            test_method='Optical Sortex'
        )

    def test_catalog_view(self):
        response = self.client.get(reverse('products:catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Premium Toor Dal')

    def test_category_filter(self):
        response = self.client.get(reverse('products:catalog'), {'category': 'dal-pulses'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Premium Toor Dal')

    def test_product_detail_view(self):
        url = reverse('products:product_detail', kwargs={
            'category_slug': self.category.slug,
            'product_slug': self.product.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Premium Toor Dal')
        self.assertContains(response, 'Optical Purity')
        self.assertContains(response, '99.7% Min')

    def test_submit_rfq_from_product(self):
        url = reverse('products:product_detail', kwargs={
            'category_slug': self.category.slug,
            'product_slug': self.product.slug
        })
        post_data = {
            'product_id': self.product.id,
            'full_name': 'Test Buyer',
            'company_name': 'Test Agri Industries',
            'email': 'buyer@testagri.in',
            'phone': '+91 99999 88888',
            'gstin': '29ABCDE1234F1Z5',
            'quantity_volume': '10 Metric Tons',
            'packaging_preference': '50kg PP Bags with Liner',
            'destination_city': 'Bengaluru',
            'destination_pincode': '560001',
            'delivery_timeline': 'Immediate',
            'notes': 'Test inquiry notes',
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(QuoteRequest.objects.filter(email='buyer@testagri.in').exists())
        rfq = QuoteRequest.objects.get(email='buyer@testagri.in')
        self.assertEqual(rfq.company_name, 'Test Agri Industries')
        self.assertEqual(rfq.product, self.product)
