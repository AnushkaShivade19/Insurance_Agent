from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# ==========================================
# 1. USER DOCUMENTS
# ==========================================
class UserDocument(models.Model):
    """
    A digital vault for users to store reusable documents.
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
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='user_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_doc_type_display()}"


# ==========================================
# 2. INSURANCE PRODUCT CATALOG
# ==========================================
class InsuranceProduct(models.Model):
    POLICY_TYPE_CHOICES = [
        ('HEALTH', 'Health Insurance'),
        ('LIFE', 'Life Insurance'),
        ('VEHICLE', 'Vehicle Insurance'),
        ('CROP', 'Crop Insurance'),
        ('PROPERTY', 'Property/Home Insurance'),
        ('LIVESTOCK', 'Livestock Insurance'),
    ]
    
    name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    # Base English Content
    description = models.TextField()
    key_features = models.TextField()
    benefits_structure = models.JSONField(default=dict, blank=True)
    base_premium = models.DecimalField(max_digits=10, decimal_places=2)
    min_entry_age = models.PositiveIntegerField(default=18)
    max_entry_age = models.PositiveIntegerField(default=65)
    brochure = models.FileField(upload_to='brochures/', blank=True, null=True)
    icon = models.ImageField(upload_to='product_icons/', blank=True, null=True) # Added icon for UI
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"

class ProductTranslation(models.Model):
    """
    Stores translations for product details in local languages.
    """
    LANGUAGE_CHOICES = [
        ('hi', 'Hindi'),
        ('mr', 'Marathi'),
        ('bn', 'Bengali'),
        ('te', 'Telugu'),
        ('ta', 'Tamil'),
        ('gu', 'Gujarati'),
        ('kn', 'Kannada'),
    ]

    product = models.ForeignKey(InsuranceProduct, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    translated_description = models.TextField()
    translated_key_features = models.TextField()
    
    class Meta:
        unique_together = ('product', 'language')

    def __str__(self):
        return f"{self.product.name} - {self.get_language_display()}"


# ==========================================
# 3. AGENT INTERACTION MODEL (New)
# ==========================================
class AgentRequest(models.Model):
    """
    Tracks user requests to talk to an agent.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONTACTED', 'Contacted'),
        ('RESOLVED', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(InsuranceProduct, on_delete=models.SET_NULL, null=True)
    request_date = models.DateTimeField(auto_now_add=True)
    preferred_language = models.CharField(max_length=50, default='English')
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Request by {self.user.username} for {self.product.name}"



# ==========================================
# 3. POLICIES & PAYMENTS
# ==========================================
class Policy(models.Model):
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
    
    policy_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=POLICY_STATUS_CHOICES, default='PENDING_APPROVAL')
    start_date = models.DateField()
    expiry_date = models.DateField()
    
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sum_assured = models.DecimalField(max_digits=12, decimal_places=2)
    premium_frequency = models.CharField(max_length=20, choices=PREMIUM_FREQ_CHOICES, default='YEARLY')
    next_payment_due_date = models.DateField(null=True, blank=True)

    nominee_name = models.CharField(max_length=100, default='Pending')
    nominee_relation = models.CharField(max_length=50, default='Other')
    nominee_age = models.PositiveIntegerField(default=18)
    policy_document = models.FileField(upload_to='policy_docs/', blank=True, null=True)

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
    PAYMENT_STATUS_CHOICES = [('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('PENDING', 'Pending')]
    PAYMENT_METHOD_CHOICES = [('UPI', 'UPI'), ('CARD', 'Credit/Debit Card'), ('NETBANKING', 'Net Banking')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)

    def __str__(self):
        return f"{self.transaction_id} ({self.status})"


# ==========================================
# 4. WEBSITE CONTENT (Articles, FAQs)
# ==========================================
class Article(models.Model):
    title = models.CharField(max_length=200)
    featured_image = models.ImageField(upload_to='article_images/')
    content = models.TextField()
    publication_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question