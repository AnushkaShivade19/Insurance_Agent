from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

# ======== 1. USER MANAGEMENT & PROFILE ========

class Profile(models.Model):
    """
    Extends the default User model to store KYC, Address, and Contact info.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Personal Details
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # Default Gender set to 'O' to prevent migration errors
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, default='O') 
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Contact & Location
    phone_number = models.CharField(max_length=15, unique=True, help_text="10-digit mobile number", blank=True, null=True)
    address = models.TextField(help_text="Full address for communication", blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    # Default pincode provided for existing rows
    pincode = models.CharField(max_length=6, help_text="Crucial for matching with local agents", blank=True, null=True, default='000000')
    
    # KYC & Identity
    aadhar_number = models.CharField(max_length=12, unique=True, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    is_kyc_verified = models.BooleanField(default=False, help_text="Has the admin verified this user's documents?")

    def __str__(self):
        return f"{self.user.username}'s Profile"

class UserDocument(models.Model):
    """
    A digital vault for users to store reusable documents (KYC, Medical Reports).
    """
    DOC_TYPE_CHOICES = [
        ('AADHAR', 'Aadhar Card'),
        ('PAN', 'PAN Card'),
        ('DL', 'Driving License'),
        ('MEDICAL', 'Medical Report'),
        ('RC', 'Vehicle RC Book'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES)
    title = models.CharField(max_length=100, help_text="e.g., 'My Blood Test Report'")
    file = models.FileField(upload_to='user_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_doc_type_display()}"


# ======== 2. INSURANCE PRODUCT CATALOG ========

class InsuranceProduct(models.Model):
    """
    Stores generic insurance plans offered by the platform.
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
    description = models.TextField(help_text="A detailed description of coverage.")
    
    # Advanced Features
    key_features = models.TextField(help_text="List key features separated by newlines.")
    benefits_structure = models.JSONField(default=dict, blank=True, help_text="JSON Data: e.g. {'room_rent': '1%', 'icu': '2%'}")
    
    # Eligibility & Pricing
    base_premium = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting premium amount.")
    min_entry_age = models.PositiveIntegerField(default=18)
    max_entry_age = models.PositiveIntegerField(default=65)
    
    # Media
    brochure = models.FileField(upload_to='brochures/', blank=True, null=True, help_text="Official PDF Brochure")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"


class ClaimStep(models.Model):
    """
    Ordered instructions for filing a claim for a specific product type.
    """
    product_type = models.CharField(max_length=20, choices=InsuranceProduct.POLICY_TYPE_CHOICES)
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()

    class Meta:
        ordering = ['product_type', 'step_number']

    def __str__(self):
        return f"{self.get_product_type_display()} - Step {self.step_number}"


# ======== 3. USER POLICIES & TRANSACTIONS ========

class Policy(models.Model):
    """
    Represents a specific policy purchased by a user.
    """
    POLICY_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('LAPSED', 'Lapsed (Payment Missed)'),
    ]
    
    PREMIUM_FREQ_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="policies")
    product = models.ForeignKey(InsuranceProduct, on_delete=models.PROTECT)
    
    # Policy Details
    policy_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=POLICY_STATUS_CHOICES, default='PENDING_APPROVAL')
    start_date = models.DateField()
    expiry_date = models.DateField()
    
    # Financials
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sum_assured = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total coverage amount.")
    premium_frequency = models.CharField(max_length=20, choices=PREMIUM_FREQ_CHOICES, default='YEARLY')
    next_payment_due_date = models.DateField(null=True, blank=True)

    # Nominee Details (Crucial for Insurance) with DEFAULTS to fix migration issues
    nominee_name = models.CharField(max_length=100, default='Pending', help_text="Full name of nominee")
    nominee_relation = models.CharField(max_length=50, default='Other', help_text="Relation to policy holder")
    nominee_age = models.PositiveIntegerField(default=18)
    
    # Documents
    policy_document = models.FileField(upload_to='policy_docs/', blank=True, null=True, help_text="The generated policy PDF")

    @property
    def is_due_for_renewal(self):
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        return (self.expiry_date >= today and 
                self.expiry_date <= thirty_days_later and
                self.status == 'ACTIVE')

    def __str__(self):
        return f"Policy {self.policy_number} - {self.user.username}"


class Payment(models.Model):
    """
    Tracks all financial transactions.
    """
    PAYMENT_STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
        ('NETBANKING', 'Net Banking'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='payments')
    
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)

    def __str__(self):
        return f"{self.transaction_id} ({self.status})"


# ======== 4. CLAIMS & SUPPORT ========

class Claim(models.Model):
    """
    Allows a user to file a claim with evidence.
    """
    CLAIM_STATUS_CHOICES = [
        ('FILED', 'Filed'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SETTLED', 'Payment Settled'),
    ]

    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="claims")
    date_filed = models.DateField(default=timezone.now)
    
    # Incident Details - DEFAULT added to fix migration
    incident_date = models.DateField(default=timezone.now, help_text="Date when the incident/illness occurred")
    description = models.TextField(help_text="Detailed description of the incident.")
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Evidence
    evidence_file = models.FileField(upload_to='claim_evidence/', blank=True, null=True, help_text="Upload bills, photos, or FIR copy")
    
    # Admin Processing
    status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='FILED')
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason if claim is rejected")
    admin_notes = models.TextField(blank=True, help_text="Internal notes for staff")

    def __str__(self):
        return f"Claim #{self.id} - Policy {self.policy.policy_number}"


class Agent(models.Model):
    """
    Stores data for local insurance agents (POSPs).
    """
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    
    # Location
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    # DEFAULT added to fix migration
    pincode = models.CharField(max_length=6, default='000000', help_text="Used to show agents near user")
    
    # Geolocation (Optional for Maps)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city}"


# ======== 5. WEBSITE CONTENT ========

class Article(models.Model):
    """
    Educational articles for the Knowledge Hub.
    """
    title = models.CharField(max_length=200)
    featured_image = models.ImageField(upload_to='article_images/')
    content = models.TextField(help_text="Full content of the article.")
    publication_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class FAQ(models.Model):
    """
    Frequently Asked Questions.
    """
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, blank=True, help_text="e.g. Claims, Payments, General")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question