import os
import sys  # <--- Added this
import django
import random
from faker import Faker

# 1. FIX: Add the project root to Python's system path
# This tells Python where to look for 'Insurance_Agent.settings'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Insurance_Agent.settings')
django.setup()

# 3. Import Models (After django.setup())
from django.contrib.auth.models import User
# Ensure 'accounts' is the app where you pasted the Agent/Profile models
from accounts.models import Profile, Agent 

# Initialize Faker with Indian Locale
fake = Faker('en_IN')

def create_users_and_profiles(n=10):
    print(f"Creating {n} Users and Profiles...")
    
    for _ in range(n):
        # Create User
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}{random.randint(1, 999)}"
        email = f"{username}@example.com"
        
        if User.objects.filter(username=username).exists():
            continue

        user = User.objects.create_user(
            username=username,
            email=email,
            password='password123',
            first_name=first_name,
            last_name=last_name
        )

        # Profile is usually created by a signal, so we just get it
        if hasattr(user, 'profile'):
            profile = user.profile
        else:
            profile = Profile.objects.create(user=user)

        profile.gender = random.choice(['M', 'F'])
        profile.date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=60)
        profile.phone_number = f"+91 {fake.msisdn()[3:]}"
        profile.address = fake.address()
        profile.city = fake.city()
        profile.state = fake.state()
        profile.pincode = fake.postcode()
        
        # Fake KYC
        profile.aadhar_number = f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
        profile.pan_number = fake.bothify(text='?????####?').upper()
        profile.is_kyc_verified = random.choice([True, False])
        
        profile.save()
        print(f" -> Created User: {username}")
def create_agents(n=20):
    print(f"\nCreating {n} Agents...")
    
    # Define mapping of Cities to States for realism
    city_state_map = {
        'Pune': 'Maharashtra', 'Mumbai': 'Maharashtra', 'Nagpur': 'Maharashtra',
        'Nashik': 'Maharashtra', 'Aurangabad': 'Maharashtra',
        'Bangalore': 'Karnataka', 'Mysore': 'Karnataka',
        'Delhi': 'Delhi', 'Chennai': 'Tamil Nadu', 'Ahmedabad': 'Gujarat'
    }
    specializations = ['Crop Insurance', 'Health', 'Life', 'Vehicle', 'Livestock']
    
    cities = list(city_state_map.keys())

    for _ in range(n):
        name = fake.name()
        location = random.choice(cities)
        state = city_state_map[location] # Automatically pick correct state
        
        langs = random.sample(['Hindi', 'Marathi', 'English', 'Gujarati', 'Kannada', 'Tamil'], k=3)
        langs_str = ", ".join(langs)
        
        Agent.objects.create(
            name=name,
            location=location,
            state=state, # NEW FIELD
            specialization=random.choice(specializations), # NEW FIELD
            languages=langs_str,
            phone_number=f"+91 {fake.msisdn()[3:]}",
            experience_years=random.randint(1, 20),
            is_verified=random.choice([True, True, False]),
            rating=round(random.uniform(3.8, 5.0), 1),
            is_active=True
        )
        print(f" -> Added {name} ({state})")