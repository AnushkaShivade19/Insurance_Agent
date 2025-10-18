# insurance/management/commands/seed_data.py

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from insurance.models import InsuranceProduct, Policy, Agent, Claim 

class Command(BaseCommand):
    help = 'Seeds the database with 10 entries for all core models (users, policies, products, agents, claims).'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Deleting old data... ---")
        User.objects.filter(is_superuser=False).delete()
        Policy.objects.all().delete()
        InsuranceProduct.objects.all().delete()
        Agent.objects.all().delete()
        Claim.objects.all().delete()

        fake = Faker('en_IN')
        NUM_ENTRIES = 10
        CITIES = ["Pune", "Nagpur", "Jaipur", "Lucknow", "Bhubaneswar", "Chennai", "Patna", "Indore", "Surat", "Kolkata"]

        self.stdout.write(f"--- 1. Creating {NUM_ENTRIES} Insurance Products... ---")
        
        # --- START OF CORRECTION ---
        # Define the base types. We will choose from this list without modifying it.
        BASE_PRODUCT_TYPES = ['HEALTH', 'LIFE', 'VEHICLE', 'CROP', 'PROPERTY', 'LIVESTOCK']
        
        products = []
        for i in range(NUM_ENTRIES):
            # Choose from the fixed list, ensuring no crash
            prod_type = random.choice(BASE_PRODUCT_TYPES) 
            
            product = InsuranceProduct.objects.create(
                # Use the product type as part of the name for better distinction
                name=f"{prod_type.capitalize()} Plan {i+1}", 
                product_type=prod_type,
                description=f"Comprehensive coverage for {prod_type.lower()} needs in rural areas.",
                key_features="Fast claim approval, No physical paperwork required.",
                base_premium=random.randint(2500, 10000)
            )
            products.append(product)
        # --- END OF CORRECTION ---

        self.stdout.write(f"--- 2. Creating {NUM_ENTRIES} Users and their Policies/Claims... ---")
        
        users = []
        for i in range(NUM_ENTRIES):
            # ... (Rest of the user creation code is correct)
            username = f'testuser{i+1}'
            user = User.objects.create_user(
                username=username,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=f'{username}@example.com'
            )
            users.append(user)

            # Create Policy for the user
            chosen_product = random.choice(products)
            start = date.today() - timedelta(days=random.randint(10, 300))
            expiry = start + timedelta(days=365)
            
            policy = Policy.objects.create(
                user=user,
                product=chosen_product,
                policy_number=f'POL-{random.randint(1000, 9999)}-{i+1}',
                start_date=start,
                expiry_date=expiry,
                premium_amount=chosen_product.base_premium + random.randint(500, 1500),
                sum_assured=random.choice([100000, 200000, 500000, 1000000]),
                status='ACTIVE' if i < 8 else 'EXPIRED'
            )
            
            # Create Claim for the policy (50% chance to have a claim)
            if random.random() > 0.5:
                 Claim.objects.create(
                    policy=policy,
                    date_filed=date.today() - timedelta(days=random.randint(1, 10)),
                    description=fake.sentence(),
                    claim_amount=policy.sum_assured * random.uniform(0.1, 0.5),
                    status=random.choice(['FILED', 'IN_REVIEW', 'APPROVED'])
                 )


        self.stdout.write(f"--- 3. Creating {NUM_ENTRIES} Agents... ---")
        for i in range(NUM_ENTRIES):
            Agent.objects.create(
                name=f"Agent {fake.last_name()}",
                phone_number=f"9{random.randint(7000000000, 9999999999)}",
                email=f"localagent{i}@insurance.com",
                address=fake.street_address(),
                city=random.choice(CITIES),
                is_active=True
            )


        self.stdout.write(self.style.SUCCESS(f'Successfully seeded the database with {NUM_ENTRIES} entries for all core models!'))