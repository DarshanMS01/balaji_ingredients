"""
core/management/commands/seed_data.py
Populates realistic industrial categories, products, specifications,
demo B2B buyer account, sample orders (24 total: 5 pending, 19 completed),
quotes, documents, notifications, and support tickets.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from core.models import SiteStat
from products.models import Category, Product, ProductSpecification, QuoteRequest
from portal.models import CompanyProfile, Order, OrderItem, B2BDocument, Notification, SupportTicket


class Command(BaseCommand):
    help = 'Seeds database with categories, industrial products, specifications, and demo portal data'

    def handle(self, *args, **options):
        self.stdout.write("Starting comprehensive database seeding...")

        # 1. Site Stats
        SiteStat.objects.all().delete()
        stats_data = [
            {'label': 'Years of Processing Heritage', 'value': '25+', 'order': 1},
            {'label': 'Verified Ingredient SKUs', 'value': '500+', 'order': 2},
            {'label': 'Annual Processing Capacity', 'value': '50,000 MT', 'order': 3},
            {'label': 'Quality & Compliance Audits', 'value': '40+', 'order': 4},
        ]
        for s in stats_data:
            SiteStat.objects.create(**s, is_active=True)
        self.stdout.write(self.style.SUCCESS("[OK] Site statistics seeded."))

        # 2. Categories
        Category.objects.all().delete()
        cat_dal = Category.objects.create(
            name='DAL & CEREALS',
            slug='dal-cereals',
            tagline='Sortex Cleaned, High-Protein Pulses for Food Processors & Industrial Mills',
            description='Carefully selected and machine-cleaned pulses sourced from prime growing regions. Dehusked, graded and sortexed for maximum uniform purity and low moisture.',
            icon='⊛',
            accent_color='#d97706',
            order=1,
            is_active=True
        )

        cat_millet = Category.objects.create(
            name='MILLET & GRAINS',
            slug='millet-grains',
            tagline='Nutrient-Rich Ancient Millets & Heavy-Grain Food Cereals',
            description='Karnataka heartland sourced whole finger millet (Ragi), Lokwan wheat, non-basmati rice, and sorghum grains with high purity and calibrated moisture.',
            icon='◻',
            accent_color='#10b981',
            order=2,
            is_active=True
        )

        cat_spices = Category.objects.create(
            name='SPICES',
            slug='spices',
            tagline='Calibrated Heat, High-ASTA & High-Curcumin Single-Origin Spices',
            description='Commercial pure spice powders manufactured from selected Guntur and Byadgi sun-dried chillies, Salem turmeric, and coriander. Zero synthetic colors.',
            icon='◈',
            accent_color='#ef4444',
            order=3,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS("[OK] 3 Main Ingredient Categories created."))

        # 3. Products
        Product.objects.all().delete()
        products_data = [
            # DAL & CEREALS
            {
                'category': cat_dal,
                'name': 'Premium Sortex Toor Dal',
                'slug': 'toor-dal',
                'subtitle': 'Double-Sortexed Yellow Pigeon Pea Split, Grade A Fatka',
                'description': 'Our flagship Toor Dal is dehusked and split with precision water-polishing. It undergoes multi-pass optical color sorting to eliminate unhusked grains, chalky kernels, and foreign matter. Delivers rapid, uniform cooking and consistent yellow dal consistency favored by industrial ready-to-eat and food service operations.',
                'grade': 'Grade A Fatka Double Sortex',
                'purity_percentage': '99.7% Min',
                'moisture_content': '< 10.0%',
                'shelf_life': '12 Months',
                'origin': 'Gulbarga (Kalaburagi), Karnataka',
                'min_order_qty': '1 Metric Ton (20 Bags of 50kg)',
                'packaging_options': '25kg & 50kg PP Bags with LDPE Liner; 1000kg FIBC Jumbo Bags',
                'unit_price': Decimal('13200.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Ready-to-Eat, Instant Dal Mixes, Dal Mills, HoReCa Institutional',
                'image_gradient': 'linear-gradient(135deg, #e6af2e 0%, #c88719 50%, #915a07 100%)',
                'is_featured': True,
                'order': 1,
                'specs': [
                    ('Optical Purity', '99.7% Min', 'Optical Sortex / Manual Count'),
                    ('Moisture Content', '9.5% - 10.5% Max', 'Halogen Moisture Analyzer'),
                    ('Foreign Matter', '< 0.10% w/w', 'IS:4333 (Part II)'),
                    ('Damaged / Discolored Grains', '< 0.5% Max', 'Visual Separation'),
                    ('Weevilled / Insect Damage', 'NIL', 'Microscopic Screening'),
                    ('Total Protein (Dry Basis)', '22.4 g / 100g', 'Kjeldahl Method (AOAC 992.23)'),
                ]
            },
            {
                'category': cat_dal,
                'name': 'Moong Dal Mogar',
                'slug': 'moong-dal',
                'subtitle': 'Easy-Digest Yellow Split Gram for Snack & Instant Food Formulations',
                'description': 'Husk-free yellow moong dal processed from prime shiny green gram. Highly digestible protein matrix with minimal gelatinization time, ideally calibrated for extrusion snacks, papad manufacture, bakery fillings, and instant dry soup mixes.',
                'grade': 'Superfine Sortex Cleaned',
                'purity_percentage': '99.8% Min',
                'moisture_content': '< 9.5%',
                'shelf_life': '12 Months',
                'origin': 'Rajasthan & Gujarat',
                'min_order_qty': '1 Metric Ton',
                'packaging_options': '25kg & 50kg PP Bags; Custom branding on request',
                'unit_price': Decimal('11800.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Namkeen & Snacks, Papad Making, Instant Soups, Health Foods',
                'image_gradient': 'linear-gradient(135deg, #f4d35e 0%, #ee964b 50%, #c46816 100%)',
                'is_featured': True,
                'order': 2,
                'specs': [
                    ('Purity Level', '99.8% Min', 'Buhler Sortex Optical'),
                    ('Cooking Time to Gelatinization', '14 - 16 Minutes', 'Standard Boiling Test'),
                    ('Protein Content', '24.1 g / 100g', 'AOAC 992.23'),
                    ('Foreign Seeds', 'NIL', 'IS:4333'),
                ]
            },
            {
                'category': cat_dal,
                'name': 'Unpolished Chana Dal',
                'slug': 'chana-dal',
                'subtitle': 'Nutrient-Intact Golden Gram Split for Besan Milling & Savory Snacks',
                'description': 'Pure unpolished Chana Dal produced from select desi chickpeas. Because no water, artificial colors, or oils are applied during splitting, the dal retains its natural nutty flavor, crisp golden color, and superior water absorption capacity for besan flour milling and savory snacks.',
                'grade': 'Desi Bold Unpolished Grade 1',
                'purity_percentage': '99.6% Min',
                'moisture_content': '< 10.5%',
                'shelf_life': '12 Months',
                'origin': 'Latur / Solapur, Maharashtra',
                'min_order_qty': '2 Metric Tons (40 Bags of 50kg)',
                'packaging_options': '50kg Food-Grade Polypropylene Sacks with Inner Poly Barrier',
                'unit_price': Decimal('8900.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Commercial Besan Flour Mills, Farsan, Namkeen, Sweets',
                'image_gradient': 'linear-gradient(135deg, #d4a373 0%, #b07d4a 50%, #7f552b 100%)',
                'is_featured': True,
                'order': 3,
                'specs': [
                    ('Sortex Purity', '99.6% Min', 'Optical Sorting'),
                    ('Moisture Content', '< 10.5% Max', 'Oven Dry Method'),
                    ('Chalky / Broken Grains', '< 1.0%', 'Grain Sieve Sizing'),
                    ('Crude Fiber', '8.2% w/w', 'AOAC 962.09'),
                    ('Aflatoxin (B1+B2+G1+G2)', '< 4.0 ppb (ND)', 'HPLC / ELISA'),
                ]
            },
            {
                'category': cat_dal,
                'name': 'Urad Dal (White Gota & Split)',
                'slug': 'urad-dal',
                'subtitle': 'High-Viscosity White Black Gram for Batter & Fermentation Systems',
                'description': 'Sortex-cleaned white whole gota and split urad dal with outstanding aeration and batter volume yield. Essential for commercial batter manufacturers, papad units, and southern breakfast premixes.',
                'grade': 'Export Grade Gota Double Polish',
                'purity_percentage': '99.8% Min',
                'moisture_content': '< 10.0%',
                'shelf_life': '12 Months',
                'origin': 'Andhra Pradesh & Myanmar Port Hubs',
                'min_order_qty': '1 Metric Ton',
                'packaging_options': '25kg & 50kg PP Bags with Liner',
                'unit_price': Decimal('12400.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Idli/Dosa Batter Production, Papad, Specialty Extrusions',
                'image_gradient': 'linear-gradient(135deg, #e5e5e5 0%, #a3a3a3 50%, #525252 100%)',
                'is_featured': False,
                'order': 4,
                'specs': [
                    ('Optical Purity', '99.8% Min', 'Optical Sortex'),
                    ('Foaming & Viscosity Yield', 'High (Optimal Mucilage)', 'Standardized Rheometer'),
                    ('Foreign Matter', '< 0.08%', 'IS:4333'),
                ]
            },

            # MILLET & GRAINS
            {
                'category': cat_millet,
                'name': 'Organic Whole Finger Millet (Ragi)',
                'slug': 'ragi',
                'subtitle': 'High-Calcium Red Millet Grains for Malting & Direct Milling',
                'description': 'Directly aggregated from non-GMO farming collectives in Southern Karnataka. Cleaned through air-screen destoners and calibrated gravity tables to remove tiny stone particles and chaff. Ideal for health food brands, malt extraction, sprouted ragi powder, and infant nutrition bases.',
                'grade': 'Grade A Bold Grain Destoned',
                'purity_percentage': '99.5% Min',
                'moisture_content': '< 10.0%',
                'shelf_life': '18 Months',
                'origin': 'Mandya & Tumakuru, Karnataka',
                'min_order_qty': '1 Metric Ton',
                'packaging_options': '50kg Moisture-Barrier PP Sacks, 500kg FIBC Bulk Bags',
                'unit_price': Decimal('4200.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Infant Nutrition, Malt Extraction, Health Drink Mixes, Bakery',
                'image_gradient': 'linear-gradient(135deg, #7f4f24 0%, #582f0e 50%, #331800 100%)',
                'is_featured': True,
                'order': 5,
                'specs': [
                    ('Calcium Content', '344 mg / 100g', 'Atomic Absorption Spectrophotometry'),
                    ('Dietary Fiber', '18.8 g / 100g', 'Enzymatic-Gravimetric Method'),
                    ('Foreign Seed Contamination', '< 0.10%', 'IS:4333'),
                    ('Moisture Retention', '< 10.0%', 'Halogen Moisture Analysis'),
                    ('Germination Capacity (for malting)', '> 92%', 'Petri Dish Germination Test'),
                ]
            },
            {
                'category': cat_millet,
                'name': 'Sharbati Lokwan Food Wheat',
                'slug': 'wheat',
                'subtitle': 'High-Gluten Golden Hard Wheat for Commercial Flour Mills & Pasta',
                'description': 'Dense golden wheat grains selected for high wet gluten and water absorption index. Free from fungal black point, weed seed contamination, or pesticide residue. Produces light, elastic dough with superior shelf performance for commercial bread, biscuits, and traditional rotis.',
                'grade': 'Grade 1 Machine Cleaned Bold Grain',
                'purity_percentage': '99.5% Min',
                'moisture_content': '< 11.0%',
                'shelf_life': '18 Months in Dry Storage',
                'origin': 'Sehore / Malwa, Madhya Pradesh',
                'min_order_qty': '5 Metric Tons (100 Bags of 50kg)',
                'packaging_options': '50kg Multiwall Sacks; Bulk Container Liner Bags (20ft FCL)',
                'unit_price': Decimal('3400.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Industrial Flour Mills, Bread & Biscuit Baking, Pasta Extrusion',
                'image_gradient': 'linear-gradient(135deg, #f3c98b 0%, #daa06d 50%, #a67c52 100%)',
                'is_featured': True,
                'order': 6,
                'specs': [
                    ('Hectolitre Test Weight', '78.5 kg/hL Min', 'Chondrometer Test'),
                    ('Wet Gluten Content', '28.0% - 31.0%', 'Glutomatic Method'),
                    ('Falling Number', '> 350 Seconds', 'Hagberg-Perten Method'),
                    ('Total Foreign Matter', '< 0.25% w/w', 'IS:4333'),
                ]
            },
            {
                'category': cat_millet,
                'name': 'Sona Masoori & Non-Basmati Rice',
                'slug': 'rice',
                'subtitle': 'Silky Sortexed Raw & Steam Rice for Institutional Processing',
                'description': 'Aromatic medium-grain non-basmati rice with low starch stickiness and uniform elongation. Milled in automated Japanese Bühler sortex lines with zero broken kernels.',
                'grade': 'Grade A Steam / Raw Sortex',
                'purity_percentage': '99.8% Min',
                'moisture_content': '< 12.0%',
                'shelf_life': '24 Months',
                'origin': 'Raichur & Kurnool Paddy Belt',
                'min_order_qty': '5 Metric Tons',
                'packaging_options': '25kg / 50kg BOPP Laminated Bags & 1 MT FIBC',
                'unit_price': Decimal('5200.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Puffed Rice, Extruded Snacks, Rice Flour, Food Service Chains',
                'image_gradient': 'linear-gradient(135deg, #fdf0d5 0%, #e8d8c8 50%, #c4b5a5 100%)',
                'is_featured': False,
                'order': 7,
                'specs': [
                    ('Sortex Purity', '99.8% Min', 'Optical CCD Camera'),
                    ('Broken Kernels', '< 2.0% Max', 'Grading Sieves'),
                    ('Moisture', '< 12.0%', 'Moisture Meter'),
                ]
            },
            {
                'category': cat_millet,
                'name': 'Commercial Sorghum (Jowar) & Millets',
                'slug': 'sorghum-millets',
                'subtitle': 'Cleaned White Sorghum & Pearl Millet for Gluten-Free Formulations',
                'description': 'Destoned and polished white jowar, bajra, and foxtail millet grains. High starch gelatinization and neutral flavour profile suitable for gluten-free formulations and extruded snacks.',
                'grade': 'Cleaned White Bold Grade 1',
                'purity_percentage': '99.4% Min',
                'moisture_content': '< 10.5%',
                'shelf_life': '12 Months',
                'origin': 'Northern Karnataka & Maharashtra',
                'min_order_qty': '2 Metric Tons',
                'packaging_options': '50kg PP Sacks with Liner',
                'unit_price': Decimal('3900.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Gluten-Free Flour Blends, Flakes, Porridge Premixes, Animal Feed',
                'image_gradient': 'linear-gradient(135deg, #e9d8a6 0%, #c2a649 50%, #947e32 100%)',
                'is_featured': False,
                'order': 8,
                'specs': [
                    ('Grain Purity', '99.4% Min', 'Gravity Destoner'),
                    ('Starch Content', '68.5% Dry Basis', 'AOAC 996.11'),
                    ('Foreign Seed Contamination', '< 0.15%', 'IS:4333'),
                ]
            },

            # SPICES
            {
                'category': cat_spices,
                'name': 'Guntur S4 Stemless Pure Chilli Powder',
                'slug': 'chilli-powder',
                'subtitle': 'High-Heat Commercial Red Chilli Powder (30,000 - 35,000 SHU)',
                'description': 'Crafted from selected, stemless Guntur S4 chillies pulverized under temperature-controlled hammermills. Delivers sharp, punchy pungency and authentic Indian red pepper aroma. 100% free from Sudan dyes, starch adulterants, and artificial oleoresins.',
                'grade': 'Stemless Grade 1 Fine Powder',
                'purity_percentage': '100% Pure Capsicum annuum',
                'moisture_content': '< 9.0%',
                'shelf_life': '12 Months',
                'origin': 'Guntur, Andhra Pradesh',
                'min_order_qty': '500 kg',
                'packaging_options': '25kg Nitrogen-Flushed Aluminum Composite Bags inside Outer PP Sacks',
                'unit_price': Decimal('38000.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Spice Blends, Seasoning Manufacturers, Marinades, Meat Processing',
                'image_gradient': 'linear-gradient(135deg, #d90429 0%, #a0001e 50%, #590004 100%)',
                'is_featured': True,
                'order': 9,
                'specs': [
                    ('Scoville Pungency (Heat)', '30,000 - 35,000 SHU', 'HPLC Capsaicinoid Determination'),
                    ('ASTA Color Value', '75 - 85 ASTA', 'Spectrophotometric (ASTA 20.1)'),
                    ('Non-Volatile Ether Extract', '> 12.0% w/w', 'FSSAI Method'),
                    ('Sudan Dyes (I, II, III, IV)', 'NOT DETECTED (< 10 ppb)', 'LC-MS/MS Screening'),
                    ('Aflatoxin B1', '< 5.0 ppb', 'HPLC Fluorescence'),
                ]
            },
            {
                'category': cat_spices,
                'name': 'Salem Pure Golden Turmeric Powder',
                'slug': 'turmeric',
                'subtitle': 'High-Curcumin (3.5%+) Micro-Milled Natural Turmeric',
                'description': 'Manufactured from selected Salem and Nizamabad mother turmeric fingers. Cryogenically ground to preserve volatile essential oils (turmerone) and bright golden color. 100% free from lead chromate and metanil yellow.',
                'grade': 'Export Grade High-Curcumin',
                'purity_percentage': '100% Pure Curcuma longa',
                'moisture_content': '< 8.5%',
                'shelf_life': '18 Months',
                'origin': 'Salem, Tamil Nadu & Nizamabad, Telangana',
                'min_order_qty': '500 kg',
                'packaging_options': '25kg Poly-lined Multiwall Kraft Sacks & Nitrogen Foil Bags',
                'unit_price': Decimal('21000.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Food Coloring & Flavors, Pharmaceutical Curcumin Extract, Curry Powders',
                'image_gradient': 'linear-gradient(135deg, #fcbf49 0%, #f77f00 50%, #d62828 100%)',
                'is_featured': True,
                'order': 10,
                'specs': [
                    ('Curcumin Content', '3.50% - 4.20% Min', 'Spectrophotometric (ASTA 18.0)'),
                    ('Volatile Essential Oil', '> 3.8% v/w', 'Clevenger Distillation'),
                    ('Total Ash', '< 6.8%', 'IS:1797'),
                    ('Heavy Metals (Lead, Cadmium)', 'Below LOQ (< 0.5 ppm)', 'ICP-MS Analysis'),
                ]
            },
            {
                'category': cat_spices,
                'name': 'Prime Green Coriander Powder (Dhania)',
                'slug': 'coriander',
                'subtitle': 'Aromatic Cool-Milled Coriander Powder with High Volatile Oil',
                'description': 'Processed from rich green Rajasthan Ramganj Mandi coriander seeds. Destoned, roasted lightly, and ground to release sweet, herbal notes with balanced linalool content.',
                'grade': 'Eagle Grade Cleaned & Ground',
                'purity_percentage': '99.5% Pure Spice',
                'moisture_content': '< 9.0%',
                'shelf_life': '12 Months',
                'origin': 'Ramganj Mandi / Kota, Rajasthan',
                'min_order_qty': '500 kg',
                'packaging_options': '25kg Nitrogen-Sealed LDPE Barrier Bags',
                'unit_price': Decimal('16500.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Curry Powders, Garam Masala, Snack Seasonings, Ready Sauces',
                'image_gradient': 'linear-gradient(135deg, #a3b18a 0%, #588157 50%, #3a5a40 100%)',
                'is_featured': False,
                'order': 11,
                'specs': [
                    ('Volatile Essential Oil', '> 0.40% v/w', 'Steam Distillation'),
                    ('Total Ash', '< 5.5%', 'IS:1797'),
                    ('Acid Insoluble Ash', '< 1.0%', 'Gravimetric Method'),
                ]
            },
            {
                'category': cat_spices,
                'name': 'Cumin Seeds & Custom Masala Systems',
                'slug': 'cumin-spice-systems',
                'subtitle': 'Machine Cleaned Cumin Seeds & Tailored Industrial Spice Formulations',
                'description': 'Sortex-cleaned Unjha Jeera and bespoke spice seasoning systems formulated to OEM client specifications. Consistent bulk flavor matrices for chips, snacks, noodles, and culinary bases.',
                'grade': 'Singapore / Europe 99.5% Purity',
                'purity_percentage': '99.5% Min',
                'moisture_content': '< 8.0%',
                'shelf_life': '12 Months',
                'origin': 'Unjha, Gujarat',
                'min_order_qty': '500 kg',
                'packaging_options': '25kg & 50kg PP Sacks with Inner Barrier',
                'unit_price': Decimal('32000.00'),
                'unit_name': 'Quintal (100 kg)',
                'applications': 'Snack Seasoning, Bakery Biscuits, Custom Culinary Pre-mixes',
                'image_gradient': 'linear-gradient(135deg, #b08968 0%, #7f5539 50%, #582f0e 100%)',
                'is_featured': False,
                'order': 12,
                'specs': [
                    ('Cumin Purity', '99.5% Min', 'Mechanical Sortex & Aspirator'),
                    ('Volatile Oil', '> 2.5% v/w', 'Clevenger'),
                    ('Aflatoxin', '< 5.0 ppb', 'HPLC'),
                ]
            },
        ]

        created_products = []
        for pdata in products_data:
            specs = pdata.pop('specs')
            product = Product.objects.create(**pdata)
            created_products.append(product)
            for idx, (pname, pval, pmethod) in enumerate(specs, start=1):
                ProductSpecification.objects.create(
                    product=product,
                    parameter_name=pname,
                    parameter_value=pval,
                    test_method=pmethod,
                    order=idx
                )
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_products)} industrial products & 45+ specifications seeded across all categories."))

        # 4. Demo User & Verified Company Profile
        demo_user, created = User.objects.get_or_create(
            username='demo_buyer',
            defaults={
                'email': 'procurement@apexagri.in',
                'first_name': 'Ramesh',
                'last_name': 'Shetty',
                'is_active': True,
            }
        )
        demo_user.set_password('Balaji@2026!')
        demo_user.email = 'procurement@apexagri.in'
        demo_user.save()

        CompanyProfile.objects.filter(user=demo_user).delete()
        profile = CompanyProfile.objects.create(
            user=demo_user,
            company_name='Apex Agro Processors Pvt Ltd',
            gstin='29AAACA9876Q1Z2',
            pan_number='AAACA9876Q',
            business_type='manufacturer',
            phone='+91 98450 11223',
            address_line1='Plot 48-A, Peenya Industrial Area 3rd Phase',
            address_line2='Near TVS Cross',
            city='Bengaluru',
            state='Karnataka',
            pincode='560058',
            is_verified=True
        )
        self.stdout.write(self.style.SUCCESS("[OK] Demo client account 'demo_buyer' (Pass: Balaji@2026!) configured."))

        # 5. Quote Requests (Active Quotes: 3)
        QuoteRequest.objects.all().delete()
        rfq1 = QuoteRequest.objects.create(
            product=created_products[0], # Toor Dal
            product_name=created_products[0].name,
            category_name=cat_dal.name,
            full_name='Ramesh Shetty',
            company_name='Apex Agro Processors Pvt Ltd',
            email='procurement@apexagri.in',
            phone='+91 98450 11223',
            gstin='29AAACA9876Q1Z2',
            quantity_volume='10 Metric Tons (200 Bags)',
            packaging_preference='50kg PP Bags with Liner',
            destination_city='Bengaluru, Karnataka',
            destination_pincode='560058',
            delivery_timeline='Within 7 days',
            notes='Grade A Fatka double sortexed required. Include batch CoA.',
            status='confirmed',
            quoted_price_per_unit=Decimal('132000.00'),
            admin_notes='Approved at ₹132,000/MT ex-warehouse.'
        )

        rfq2 = QuoteRequest.objects.create(
            product=created_products[4], # Whole Ragi
            product_name=created_products[4].name,
            category_name=cat_millet.name,
            full_name='Ramesh Shetty',
            company_name='Apex Agro Processors Pvt Ltd',
            email='procurement@apexagri.in',
            phone='+91 98450 11223',
            gstin='29AAACA9876Q1Z2',
            quantity_volume='15 Metric Tons',
            packaging_preference='50kg Moisture-Barrier PP Sacks',
            destination_city='Bengaluru, Karnataka',
            destination_pincode='560058',
            delivery_timeline='Monthly recurring contract',
            notes='Destoned high-calcium ragi grain with moisture strictly <10%.',
            status='quoted',
            quoted_price_per_unit=Decimal('42000.00'),
            admin_notes='Quotation issued with commercial volume discount.'
        )

        rfq3 = QuoteRequest.objects.create(
            product=created_products[8], # Guntur Chilli Powder
            product_name=created_products[8].name,
            category_name=cat_spices.name,
            full_name='Ramesh Shetty',
            company_name='Apex Agro Processors Pvt Ltd',
            email='procurement@apexagri.in',
            phone='+91 98450 11223',
            gstin='29AAACA9876Q1Z2',
            quantity_volume='2 Metric Tons (80 Bags of 25kg)',
            packaging_preference='25kg Nitrogen-Flushed Aluminum Foil in Cartons',
            destination_city='Bengaluru, Karnataka',
            destination_pincode='560058',
            delivery_timeline='Within 14 days',
            notes='Target 32,000 SHU with verified zero Sudan dye report.',
            status='new',
            quoted_price_per_unit=Decimal('380000.00'),
            admin_notes='Sample sent for lab inspection.'
        )
        self.stdout.write(self.style.SUCCESS("[OK] 3 Active Quotes created."))

        # 6. Commercial Orders (24 Total: 5 Pending/Processing/Shipped, 19 Completed/Delivered)
        Order.objects.all().delete()
        
        # Order 1: Dispatched (Active)
        o1 = Order.objects.create(
            user=demo_user,
            quote_request=rfq1,
            order_number='BI-ORD-2048',
            status='dispatched',
            payment_status='advance_paid',
            subtotal=Decimal('1320000.00'),
            tax_amount=Decimal('66000.00'),
            total_amount=Decimal('1386000.00'),
            advance_amount=Decimal('200000.00'),
            carrier_name='VRL Logistics Commercial Freight',
            tracking_consignment_no='VRL-BLR-998821',
            vehicle_number='KA-04-E-4890',
            dispatch_date=date.today() - timedelta(days=1),
            expected_delivery_date=date.today() + timedelta(days=1),
            shipping_address='Plot 48-A, Peenya Industrial Area 3rd Phase, Bengaluru 560058',
            customer_notes='Gate entry between 8 AM and 6 PM. Forklift unloading available.',
            admin_notes='Sortex lot #TD-2026-09A in transit. Weighbridge slip attached.'
        )
        OrderItem.objects.create(
            order=o1, product=created_products[0], product_name=created_products[0].name,
            quantity=Decimal('10.00'), unit='Metric Tons', packaging='50kg PP Bags with LDPE Liner (200 Bags)',
            unit_price=Decimal('132000.00'), total_price=Decimal('1320000.00')
        )

        # Order 2: Processing (Active)
        o2 = Order.objects.create(
            user=demo_user,
            order_number='BI-ORD-2049',
            status='processing',
            payment_status='advance_paid',
            subtotal=Decimal('630000.00'),
            tax_amount=Decimal('31500.00'),
            total_amount=Decimal('661500.00'),
            advance_amount=Decimal('100000.00'),
            carrier_name='Safechem Express',
            tracking_consignment_no='SAF-BLR-5520',
            vehicle_number='KA-01-AB-8832',
            dispatch_date=date.today(),
            expected_delivery_date=date.today() + timedelta(days=3),
            shipping_address='Plot 48-A, Peenya Industrial Area 3rd Phase, Bengaluru 560058',
            customer_notes='Destoned ragi grain for formulation line 2.',
            admin_notes='Optical sortex cleaning batch 4 completed.'
        )
        OrderItem.objects.create(
            order=o2, product=created_products[4], product_name=created_products[4].name,
            quantity=Decimal('15.00'), unit='Metric Tons', packaging='50kg Moisture-Barrier PP Sacks (300 Bags)',
            unit_price=Decimal('42000.00'), total_price=Decimal('630000.00')
        )

        # Order 3: Pending Approval
        o3 = Order.objects.create(
            user=demo_user,
            order_number='BI-ORD-2050',
            status='pending',
            payment_status='unpaid',
            subtotal=Decimal('760000.00'),
            tax_amount=Decimal('38000.00'),
            total_amount=Decimal('798000.00'),
            shipping_address='Plot 48-A, Peenya Industrial Area 3rd Phase, Bengaluru 560058',
            customer_notes='Guntur chilli powder 35k SHU batch.',
            admin_notes='Awaiting token advance verification.'
        )
        OrderItem.objects.create(
            order=o3, product=created_products[8], product_name=created_products[8].name,
            quantity=Decimal('2.00'), unit='Metric Tons', packaging='25kg Nitrogen-Flushed Aluminum Foil Bags',
            unit_price=Decimal('380000.00'), total_price=Decimal('760000.00')
        )

        # Order 4: Quote Confirmed
        o4 = Order.objects.create(
            user=demo_user,
            order_number='BI-ORD-2051',
            status='quote_confirmed',
            payment_status='unpaid',
            subtotal=Decimal('420000.00'),
            tax_amount=Decimal('21000.00'),
            total_amount=Decimal('441000.00'),
            shipping_address='Plot 48-A, Peenya Industrial Area 3rd Phase, Bengaluru 560058',
            customer_notes='Salem turmeric powder 3.8% Curcumin.',
        )
        OrderItem.objects.create(
            order=o4, product=created_products[9], product_name=created_products[9].name,
            quantity=Decimal('2.00'), unit='Metric Tons', packaging='25kg Kraft Bags with Liner',
            unit_price=Decimal('210000.00'), total_price=Decimal('420000.00')
        )

        # Order 5: Processing (Active)
        o5 = Order.objects.create(
            user=demo_user,
            order_number='BI-ORD-2052',
            status='processing',
            payment_status='advance_paid',
            subtotal=Decimal('356000.00'),
            tax_amount=Decimal('17800.00'),
            total_amount=Decimal('373800.00'),
            shipping_address='Plot 48-A, Peenya Industrial Area 3rd Phase, Bengaluru 560058',
            customer_notes='Unpolished Chana Dal for milling.',
        )
        OrderItem.objects.create(
            order=o5, product=created_products[2], product_name=created_products[2].name,
            quantity=Decimal('4.00'), unit='Metric Tons', packaging='50kg PP Bags (80 Bags)',
            unit_price=Decimal('89000.00'), total_price=Decimal('356000.00')
        )

        # 19 Completed Orders (Delivered historical records to total 24)
        for i in range(1, 20):
            p_idx = (i % len(created_products))
            prod = created_products[p_idx]
            order_num = f"BI-ORD-{1000 + i}"
            days_ago = 15 + (i * 12)
            sub = prod.unit_price * Decimal(str(20 + (i * 2)))
            tax = sub * Decimal('0.05')
            tot = sub + tax
            ord_c = Order.objects.create(
                user=demo_user,
                order_number=order_num,
                status='delivered',
                payment_status='fully_paid',
                subtotal=sub,
                tax_amount=tax,
                total_amount=tot,
                advance_amount=tot,
                carrier_name='VRL Logistics Commercial Freight',
                tracking_consignment_no=f'VRL-DEL-{8800+i}',
                vehicle_number=f'KA-04-E-{3000+i}',
                dispatch_date=date.today() - timedelta(days=days_ago + 3),
                expected_delivery_date=date.today() - timedelta(days=days_ago),
                shipping_address='Plot 48-A, Peenya Industrial Area 3rd Phase, Bengaluru 560058',
                admin_notes=f'Consignment #{order_num} delivered with clean proof of delivery.'
            )
            OrderItem.objects.create(
                order=ord_c,
                product=prod,
                product_name=prod.name,
                quantity=Decimal('5.00'),
                unit='Metric Tons',
                packaging='50kg PP Bags with Liner',
                unit_price=prod.unit_price * 10,
                total_price=sub
            )

        self.stdout.write(self.style.SUCCESS("[OK] 24 Commercial Orders (5 Pending/Processing/Shipped + 19 Completed) created."))

        # 7. B2B Documents
        B2BDocument.objects.all().delete()
        docs_data = [
            {'title': 'Premium Sortex Toor Dal - Technical Spec Sheet', 'doc_type': 'spec_sheet', 'category': 'DAL & CEREALS', 'doc_number': 'SPEC-TD-2026', 'file_size': '1.4 MB PDF'},
            {'title': 'Organic Whole Finger Millet (Ragi) - Certificate of Analysis (COA)', 'doc_type': 'quality_report', 'category': 'MILLET & GRAINS', 'doc_number': 'COA-RAGI-409', 'file_size': '890 KB PDF'},
            {'title': 'Guntur S4 Chilli Powder - NABL Pesticide & Sudan Dye Report', 'doc_type': 'quality_report', 'category': 'SPICES', 'doc_number': 'NABL-CHL-992', 'file_size': '1.8 MB PDF'},
            {'title': 'FSSAI Central Food Safety License (Valid till 2030)', 'doc_type': 'certificate', 'category': 'Regulatory Compliance', 'doc_number': 'FSSAI-10019043002811', 'file_size': '2.1 MB PDF'},
            {'title': 'ISO 22000:2018 Food Safety Management System Certificate', 'doc_type': 'certificate', 'category': 'Quality Management', 'doc_number': 'ISO-FSMS-2026', 'file_size': '1.6 MB PDF'},
            {'title': 'HACCP & GMP Certification of Processing Facility', 'doc_type': 'certificate', 'category': 'Plant Audit', 'doc_number': 'HACCP-IND-884', 'file_size': '1.2 MB PDF'},
            {'title': 'Proforma Invoice #BI-ORD-2048 (Apex Agro Processors)', 'doc_type': 'invoice', 'category': 'Commercial Orders', 'doc_number': 'INV-BI-2048', 'file_size': '650 KB PDF'},
            {'title': 'Formal Quotation #BI-RFQ-1024 - Sortex Dal & Spices', 'doc_type': 'quote_doc', 'category': 'Quotations', 'doc_number': 'RFQ-DOC-1024', 'file_size': '780 KB PDF'},
            {'title': 'Master Purchase Order Agreement (B2B Supply Terms)', 'doc_type': 'purchase_order', 'category': 'Legal & Contracts', 'doc_number': 'PO-MSTR-2026', 'file_size': '1.5 MB PDF'},
        ]
        for d in docs_data:
            B2BDocument.objects.create(user=demo_user, **d)
        self.stdout.write(self.style.SUCCESS("[OK] 9 B2B Technical & Regulatory Documents seeded."))

        # 8. Notifications
        Notification.objects.all().delete()
        notifs_data = [
            {'title': 'Quote Request #BI1024 Received', 'message': 'Your quote request for 10 MT Premium Toor Dal has been reviewed and commercial pricing is ready.', 'icon': 'file-text', 'link': '/quotes'},
            {'title': 'Consignment #BI-ORD-2048 Shipped', 'message': 'Your order has departed Kalaburagi processing unit via VRL Logistics (LR #VRL-BLR-998821).', 'icon': 'truck', 'link': '/orders'},
            {'title': 'New NABL Quality COA Available', 'message': 'Batch #TD-2026-09A full chromatographic test report is ready for download in your documents.', 'icon': 'shield-check', 'link': '/documents'},
            {'title': 'Quotation Price Updated', 'message': 'Volume tier discount has been applied to your Whole Ragi procurement contract.', 'icon': 'tag', 'link': '/quotes'},
        ]
        for n in notifs_data:
            Notification.objects.create(user=demo_user, **n)
        self.stdout.write(self.style.SUCCESS("[OK] 4 System Notifications seeded."))

        # 9. Support Tickets
        SupportTicket.objects.all().delete()
        SupportTicket.objects.create(
            ticket_id='TICK-1082',
            user=demo_user,
            name='Ramesh Shetty',
            email='procurement@apexagri.in',
            phone='+91 98450 11223',
            order_id='BI-ORD-2048',
            support_type='order',
            subject='ETA Verification for Peenya Unloading Ramp',
            message='Kindly confirm the exact driver contact number for the KA-04-E-4890 vehicle before it reaches Bangalore outer ring road.',
            status='open',
            admin_response='Logistics desk has notified driver; transit updates will be pushed via SMS.'
        )
        self.stdout.write(self.style.SUCCESS("[OK] Support tickets seeded."))

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] ALL BALAJI INGREDIENTS PRODUCTION SEED DATA LOADED!"))
        self.stdout.write("Credentials: Username: demo_buyer | Password: Balaji@2026! | Email: procurement@apexagri.in")
