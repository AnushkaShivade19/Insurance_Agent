# insurance/admin.py

from django.contrib import admin
from .models import Profile, InsuranceProduct, Policy, Claim, FAQ

# ... (ProfileAdmin, InsuranceProductAdmin, PolicyAdmin are correct) ...

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    # This is the line to fix
    list_display = ('id', 'policy', 'claim_amount', 'status', 'date_filed') # Changed 'amount' to 'claim_amount'
    list_filter = ('status',)
    search_fields = ('policy__policy_number',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active')
    list_filter = ('is_active',)