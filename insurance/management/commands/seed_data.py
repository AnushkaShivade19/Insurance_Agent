# insurance/management/commands/seed_data.py

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from insurance.models import InsuranceProduct, Policy

class Command(BaseCommand):
    help = 'Seeds the database with dummy data for users and policies.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old data...")
        # Clear existing data to avoid duplicates
        User.objects.filter(is_superuser=False).delete()
        Policy.objects.all().delete()
        InsuranceProduct.objects.all().delete()

        fake = Faker('en_IN') # Use Indian locale for names

        self.stdout.write("Creating new insurance products...")
        product1 = InsuranceProduct.objects.create(
            name="Gramin Health Shield",
            product_type="HEALTH",
            description="Basic health coverage.",
            key_features="Coverage up to 2 lakhs.",
            base_premium=5000
        )
        product2 = InsuranceProduct.objects.create(
            name="Kisan Crop Protection",
            product_type="CROP",
            description="Protection against crop failure.",
            key_features="Covers drought and floods.",
            base_premium=3000
        )
        products = [product1, product2]

        self.stdout.write("Creating 10 dummy users and their policies...")
        for i in range(1, 11):
            # Create User
            username = f'user{i}'
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f'{username}@example.com'
            user = User.objects.create_user(
                username=username,
                password='password123',
                first_name=first_name,
                last_name=last_name,
                email=email
            )

            # Create Policy for the user
            chosen_product = random.choice(products)
            start = date.today() - timedelta(days=random.randint(0, 300))
            
            Policy.objects.create(
                user=user,
                product=chosen_product,
                policy_number=f'POL-{random.randint(1000, 9999)}-{i}',
                start_date=start,
                expiry_date=start + timedelta(days=365),
                premium_amount=chosen_product.base_premium + random.randint(500, 1500),
                sum_assured=random.choice([100000, 200000, 500000]),
                status='ACTIVE'
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database!'))