from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
# ======== 1. USER MANAGEMENT MODELS ========

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, help_text="Full address for communication", blank=True, null=True) # ADD null=True, blank=True
    phone_number = models.CharField(max_length=15, unique=True, help_text="10-digit mobile number", blank=True, null=True) # ADD null=True, blank=True
    date_of_birth = models.DateField(blank=True, null=True) # <-- FIX: ADD null=True, blank=True
    aadhar_number = models.CharField(max_length=12, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# ======== 2. INSURANCE PRODUCT CATALOG ========

class InsuranceProduct(models.Model):
    """
    Stores details about the generic insurance plans you offer (the catalog).
    """
    POLICY_TYPE_CHOICES = [
        ('HEALTH', 'Health Insurance'),
        ('LIFE', 'Life Insurance'),
        ('VEHICLE', 'Vehicle Insurance'),
        ('CROP', 'Crop Insurance'),
        ('PROPERTY', 'Property/Home Insurance'),
        ('LIVESTOCK', 'Livestock Insurance'),
    ]
    
    name = models.CharField(max_length=100, help_text="e.g., Gramin Health Shield")
    product_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    description = models.TextField(help_text="A simple, detailed description of what this insurance covers.")
    key_features = models.TextField(help_text="List key features, separated by newlines for easy display.")
    base_premium = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting premium amount.")
    is_active = models.BooleanField(default=True, help_text="Is this product currently offered?")

    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"

# ======== 3. USER-SPECIFIC INSURANCE DATA ========

class Policy(models.Model):
    """
    Represents a specific insurance policy purchased by a user.
    This links a User to an InsuranceProduct.
    """
    POLICY_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING_APPROVAL', 'Pending Approval'),
    ]
    @property
    def is_due_for_renewal(self):
        # Checks if the expiry date is within 30 days and the status is ACTIVE
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        return (self.expiry_date >= today and 
                self.expiry_date <= thirty_days_later and
                self.status == 'ACTIVE')

    def __str__(self):
        return f"Policy {self.policy_number} for {self.user.username}"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="policies")
    product = models.ForeignKey(InsuranceProduct, on_delete=models.PROTECT, help_text="The type of product this policy is based on.")
    
    policy_number = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    expiry_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sum_assured = models.DecimalField(max_digits=12, decimal_places=2, help_text="The total coverage amount.")
    status = models.CharField(max_length=20, choices=POLICY_STATUS_CHOICES, default='PENDING_APPROVAL')

    def __str__(self):
        return f"Policy {self.policy_number} for {self.user.username}"

# ======== 4. SUPPORT & INTERACTION MODELS ========

class Claim(models.Model):
    """
    Allows a user to file a claim against one of their active policies.
    """
    CLAIM_STATUS_CHOICES = [
        ('FILED', 'Filed'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="claims")
    date_filed = models.DateField(default=timezone.now)
    description = models.TextField(help_text="Detailed description of the incident for the claim.")
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='FILED')

    def __str__(self):
        return f"Claim #{self.id} for Policy {self.policy.policy_number}"

# ======== 5. WEBSITE CONTENT MODELS ========

class FAQ(models.Model):
    """
    A simple model to store Frequently Asked Questions for a section on your website.
    """
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

class Agent(models.Model):
    """
    Stores data for local insurance agents who can assist users.
    Includes location fields for future mapping integration.
    """
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, help_text="Agent's direct contact number")
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    # Location fields for future mapping (optional, but good practice)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city}"