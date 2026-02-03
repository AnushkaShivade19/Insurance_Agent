from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# ==========================================
# 1. USER PROFILE (KYC & Contact)
# ==========================================
class Profile(models.Model):
    """
    Extends the default User model to store KYC, Address, and Contact info.
    """
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Details
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, default='O') 
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Contact & Location
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="10-digit mobile number")
    address = models.TextField(blank=True, null=True, help_text="Full address for communication")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True, default='000000')
    
    # KYC & Identity
    aadhar_number = models.CharField(max_length=12, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    is_kyc_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# ==========================================
# 2. AGENTS (POSP)
# ==========================================
class Agent(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='agent_photos/', default='agent_photos/default_agent.png')
    
    # Location
    location = models.CharField(max_length=100, help_text="City or District (e.g., Pune)")
    
    # --- NEW FIELDS FOR FILTERING ---
    state = models.CharField(max_length=50, default="Maharashtra", help_text="State (e.g. Maharashtra)")
    specialization = models.CharField(max_length=100, default="General Insurance", help_text="Main expertise (e.g. Crop, Health)")
    # --------------------------------
    
    languages = models.CharField(max_length=200, help_text="Comma separated (e.g., Hindi, Marathi)")
    phone_number = models.CharField(max_length=15)
    experience_years = models.IntegerField(default=1)
    
    # Status & Metrics
    is_verified = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    is_active = models.BooleanField(default=True)

    # Geolocation (Optional for Maps)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        # FIX: Changed self.city to self.location to prevent the crash
        return f"{self.name} - {self.location}"