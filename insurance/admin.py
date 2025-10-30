# insurance/admin.py

from django.contrib import admin
from .models import Profile, InsuranceProduct, Policy, Claim, FAQ, Agent , Article, ClaimStep

@admin.register(ClaimStep)
class ClaimStepAdmin(admin.ModelAdmin):
    list_display = ('product_type', 'step_number', 'title')
    list_filter = ('product_type',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'is_active')
    list_filter = ('is_active',)
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

@admin.register(Agent) # --- ADD THIS NEW CLASS ---
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'city', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'city', 'phone_number')