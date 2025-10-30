import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker

# Import all of your models
from insurance.models import (
    Profile, InsuranceProduct, Policy, Claim, Agent, FAQ, Article, ClaimStep
)

class Command(BaseCommand):
    help = 'Seeds the database with a complete set of dummy data for all models.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("--- Deleting old data... ---"))
        # Clear all data to ensure a clean slate (keeps superusers)
        User.objects.filter(is_superuser=False).delete()
        InsuranceProduct.objects.all().delete()
        Agent.objects.all().delete()
        FAQ.objects.all().delete()
        Article.objects.all().delete()
        ClaimStep.objects.all().delete()
        # Note: Policies and Claims are deleted automatically when Users are deleted due to CASCADE.

        fake = Faker('en_IN')  # Use Indian locale for realistic data
        
        # --- 1. Create Insurance Products ---
        self.stdout.write(self.style.SUCCESS("--- Creating Insurance Products... ---"))
        product_types = ['HEALTH', 'LIFE', 'VEHICLE', 'CROP', 'PROPERTY', 'LIVESTOCK']
        products = []
        for prod_type in product_types:
            product = InsuranceProduct.objects.create(
                name=f"{prod_type.capitalize()} Suraksha Plan",
                product_type=prod_type,
                description=f"A comprehensive {prod_type.lower()} insurance plan designed for rural needs, ensuring your family's financial security.",
                key_features=f"Complete {prod_type.lower()} coverage.\nEasy claim process.\nLow premium.",
                base_premium=random.randint(2000, 15000)
            )
            products.append(product)

        # --- 2. Create Users, Profiles, Policies, and Claims ---
        self.stdout.write(self.style.SUCCESS("--- Creating 15 Users with Profiles, Policies, and Claims... ---"))
        for i in range(15):
            first_name = fake.first_name()
            last_name = fake.last_name()
            user = User.objects.create_user(
                username=f'user{i+1}',
                password='password123',
                first_name=first_name,
                last_name=last_name,
                email=f'{first_name.lower()}.{last_name.lower()}@example.com'
            )
            Profile.objects.create(
                user=user,
                address=fake.address(),
                phone_number=fake.phone_number(),
                date_of_birth=fake.date_of_birth(minimum_age=20, maximum_age=65)
            )

            # Create 1 or 2 policies for each user
            for _ in range(random.randint(1, 2)):
                chosen_product = random.choice(products)
                start = date.today() - timedelta(days=random.randint(10, 500))
                policy = Policy.objects.create(
                    user=user,
                    product=chosen_product,
                    policy_number=f'POL-{random.randint(10000, 99999)}-{i+1}',
                    start_date=start,
                    expiry_date=start + timedelta(days=365),
                    premium_amount=chosen_product.base_premium + random.randint(500, 2500),
                    sum_assured=random.choice([100000, 200000, 500000, 1000000]),
                    status='ACTIVE' if (start + timedelta(days=365)) > date.today() else 'EXPIRED'
                )
                # Create a claim for ~50% of active policies
                if policy.status == 'ACTIVE' and random.random() > 0.5:
                    Claim.objects.create(
                        policy=policy,
                        date_filed=date.today() - timedelta(days=random.randint(1, 20)),
                        description=f"Claim filed due to {fake.word()}.",
                        claim_amount=policy.sum_assured * random.uniform(0.05, 0.2),
                        status=random.choice(['FILED', 'IN_REVIEW', 'APPROVED', 'REJECTED'])
                    )

        # --- 3. Create Agents ---
        self.stdout.write(self.style.SUCCESS("--- Creating 10 Local Agents... ---"))
        cities = ["Pune", "Nagpur", "Jaipur", "Lucknow", "Bhubaneswar", "Chennai", "Patna", "Indore", "Surat", "Kolkata"]
        for city in cities:
            Agent.objects.create(
                name=f"{fake.first_name()} {fake.last_name()}",
                phone_number=fake.phone_number(),
                email=fake.email(),
                address=fake.street_address(),
                city=city,
                is_active=True,
                latitude=fake.latitude(),
                longitude=fake.longitude()
            )

        # --- 4. Create FAQs ---
        self.stdout.write(self.style.SUCCESS("--- Creating FAQs... ---"))
        faq_data = [
            ("What is a premium?", "A premium is the fixed amount of money you pay regularly (monthly or yearly) to an insurance company to keep your policy active."),
            ("What does 'sum assured' mean?", "Sum assured is the guaranteed amount of money that the insurance company will pay out in case of an insured event, like an accident or death."),
            ("What is a deductible?", "A deductible is the initial amount you must pay out-of-pocket for a covered expense before the insurance company starts to pay."),
            ("How do I file a claim?", "You can start the claim process from your dashboard. Click on the 'File Claim' button on your active policy and follow the steps."),
            ("Why is health insurance important?", "Health insurance protects you from high, unexpected medical costs. It ensures you can get quality medical care without worrying about the financial burden.")
        ]
        for q, a in faq_data:
            FAQ.objects.create(question=q, answer=a)
        
        # --- 5. Create Articles ---
        # NOTE: This creates Article objects but does not create actual image files.
        # The image URLs will be broken unless you manually upload images with the same names.
        self.stdout.write(self.style.SUCCESS("--- Creating sample Articles... ---"))
        article_data = [
            ("Understanding Crop Insurance", "article_crop.jpg", "Crop insurance is vital for farmers..."),
            ("Choosing Your First Health Policy", "article_health.jpg", "When buying health insurance for the first time..."),
            ("Benefits of Life Insurance", "article_life.jpg", "Life insurance provides a safety net for your family...")
        ]
        for title, img_path, content in article_data:
            Article.objects.create(title=title, featured_image=f'article_images/{img_path}', content=content)

        # --- 6. Create Claim Steps ---
        self.stdout.write(self.style.SUCCESS("--- Creating Claim Guidance Steps... ---"))
        ClaimStep.objects.create(product_type='VEHICLE', step_number=1, title="File an FIR", description="For theft or major accidents, immediately file a First Information Report (FIR) at the nearest police station and get a copy.")
        ClaimStep.objects.create(product_type='VEHICLE', step_number=2, title="Inform BimaSakhi", description="Call our helpline or your agent within 24 hours to report the incident.")
        ClaimStep.objects.create(product_type='VEHICLE', step_number=3, title="Document Submission", description="Submit photos of the damage, a copy of the FIR, and your vehicle's RC book through your dashboard or to your agent.")
        ClaimStep.objects.create(product_type='HEALTH', step_number=1, title="Hospital Admission", description="Inform the hospital's insurance desk about your BimaSakhi policy. They will assist with cashless procedures if the hospital is in our network.")
        ClaimStep.objects.create(product_type='HEALTH', step_number=2, title="Emergency Contact", description="In case of an emergency, get admitted first and then inform us within 48 hours by calling our helpline.")

        self.stdout.write(self.style.SUCCESS('>>>> Database seeding complete! <<<<'))