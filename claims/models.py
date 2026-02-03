from django.db import models
from insurance.models import Policy # Import Policy from your main app

class Claim(models.Model):
    STATUS_CHOICES = [
        ('FILED', 'Filed'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='claims')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FILED')
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Evidence
    evidence_image = models.ImageField(upload_to='claims/evidence/', blank=False, help_text="Upload a photo of the incident")
    
    # Description (Filled via Voice-to-Text)
    description = models.TextField(blank=True, help_text="Describe incident details")
    
    date_filed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Claim #{self.id} - {self.policy.policy_number}"

class ClaimStep(models.Model):
    """Guidance steps shown to user based on product type"""
    product_type = models.CharField(max_length=50) 
    step_number = models.IntegerField()
    description = models.TextField()

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"{self.product_type} - Step {self.step_number}"