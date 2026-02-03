import random
from decimal import Decimal
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

# CHANGE THIS to your actual app name
from insurance.models import (
    Profile, InsuranceProduct, Policy, Payment, Agent, Article, FAQ, UserDocument
)

# Initialize Faker with Indian Locale for realistic data
fake = Faker('en_IN')

class Command(BaseCommand):
    help = "Seeds the database with realistic dummy data for BimaSakhi"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Deleting old data...'))
        # Order matters to avoid foreign key errors
        Payment.objects.all().delete()
        Policy.objects.all().delete()
        UserDocument.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete() # Keep admin
        Agent.objects.all().delete()
        InsuranceProduct.objects.all().delete()
        Article.objects.all().delete()
        FAQ.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Creating new data...'))

        # --- 1. CREATE INSURANCE PRODUCTS (Static realistic data) ---
        products = [
            {
                "name": "Gramin Suraksha Health Plan",
                "type": "HEALTH",
                "desc": "Comprehensive health coverage for rural families covering hospitalization and critical illness.",
                "premium": 4500.00
            },
            {
                "name": "Kisan Fasal Bima Yojana",
                "type": "CROP",
                "desc": "Protects farmers against crop loss due to natural calamities, pests, and diseases.",
                "premium": 1200.00
            },
            {
                "name": "Sampoorna Jeevan Life Cover",
                "type": "LIFE",
                "desc": "Term life insurance providing financial security to your family in your absence.",
                "premium": 8000.00
            },
            {
                "name": "Pashu Dhan Raksha (Livestock)",
                "type": "LIVESTOCK",
                "desc": "Insurance cover for cattle and livestock against accidental death and diseases.",
                "premium": 2500.00
            },
            {
                "name": "Tractor & Vehicle Shield",
                "type": "VEHICLE",
                "desc": "Complete protection for your tractor and two-wheelers against accidents and theft.",
                "premium": 3500.00
            }
        ]

        db_products = []
        for p in products:
            prod = InsuranceProduct.objects.create(
                name=p["name"],
                product_type=p["type"],
                description=p["desc"],
                key_features="Cashless Treatment\n24x7 Support\nLow Premium",
                base_premium=p["premium"],
                min_entry_age=18,
                max_entry_age=70,
                is_active=True
            )
            db_products.append(prod)
        self.stdout.write(f"Created {len(db_products)} Products.")

        # --- 2. CREATE AGENTS ---
        for _ in range(10):
            Agent.objects.create(
                name=fake.name(),
                phone_number=fake.phone_number(),
                email=fake.email(),
                address=fake.address(),
                city=fake.city(),
                state=fake.state(),
                pincode=fake.postcode(),
                is_active=True
            )
        self.stdout.write("Created 10 Agents.")

        # --- 3. CREATE USERS & PROFILES ---
        users = []
        for _ in range(20): # Create 20 dummy users
            # Create User
            username = fake.user_name()
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = fake.user_name() + str(random.randint(1, 1000))
            
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password="password123", # Default password for testing
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)

            # Create Profile
            Profile.objects.create(
                user=user,
                gender=random.choice(['M', 'F']),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                phone_number=fake.phone_number(),
                address=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                pincode=fake.postcode(),
                aadhar_number=fake.aadhaar_id(),
                pan_number=fake.bothify(text='????#####?').upper(), # Regex for PAN
                is_kyc_verified=random.choice([True, False])
            )
        self.stdout.write(f"Created {len(users)} Users.")

        # --- 4. CREATE POLICIES & PAYMENTS ---
        status_choices = ['ACTIVE', 'EXPIRED', 'PENDING_APPROVAL']
        
        for user in users:
            # Assign 1 to 3 policies per user randomly
            for _ in range(random.randint(1, 3)):
                product = random.choice(db_products)
                start_date = fake.date_between(start_date='-2y', end_date='today')
                expiry_date = start_date + timedelta(days=365)
                
                status = random.choice(status_choices)
                
                policy = Policy.objects.create(
                    user=user,
                    product=product,
                    policy_number=fake.unique.bothify(text='POL-#####-????').upper(),
                    status=status,
                    start_date=start_date,
                    expiry_date=expiry_date,
                    premium_amount=product.base_premium,
                    sum_assured=product.base_premium * 100, # Approx logic
                    premium_frequency='YEARLY',
                    nominee_name=fake.name(),
                    nominee_relation=random.choice(['Spouse', 'Child', 'Parent']),
                    nominee_age=random.randint(5, 60)
                )

                # Create a Payment if policy is Active
                if status == 'ACTIVE':
                    Payment.objects.create(
                        user=user,
                        policy=policy,
                        transaction_id=fake.unique.bothify(text='TXN#######'),
                        amount=policy.premium_amount,
                        status='SUCCESS',
                        payment_method=random.choice(['UPI', 'CARD', 'NETBANKING'])
                    )

        self.stdout.write("Created Policies and Payments.")

        # --- 5. CREATE KNOWLEDGE HUB (FAQs & Articles) ---
        faq_data = [
            ("How do I claim insurance?", "Go to dashboard, click 'File Claim', upload photo."),
            ("What is the age limit?", "Usually 18 to 65 years depending on the plan."),
            ("Can I pay via UPI?", "Yes, we support BHIM UPI, GPay, and PhonePe.")
        ]
        for q, a in faq_data:
            FAQ.objects.create(question=q, answer=a, category="General")

        Article.objects.create(
            title="Why Crop Insurance is Essential for Farmers",
            content=fake.paragraph(nb_sentences=10),
            featured_image=None # Skipping image file handling for simplicity
        )
        Article.objects.create(
            title="Understanding Term Life Insurance",
            content=fake.paragraph(nb_sentences=10),
            featured_image=None
        )
        self.stdout.write("Created FAQs and Articles.")

        self.stdout.write(self.style.SUCCESS("DATABASE SEEDING COMPLETED SUCCESSFULLY!"))