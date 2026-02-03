# insurance/admin.py

from django.contrib import admin
from .models import InsuranceProduct, Policy, FAQ, Article

from django.contrib import admin
from .models import (
    InsuranceProduct, ProductTranslation, AgentRequest, 
    Policy, Payment, Article, FAQ
)

# Register core models
# Custom Admin for Policy (Optional: makes the list view nicer)
@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'user', 'product', 'status', 'start_date')
    list_filter = ('status', 'product')
    search_fields = ('policy_number', 'user__username')

@admin.register(AgentRequest)
class AgentRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'status', 'request_date')
    list_filter = ('status',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active')
    list_filter = ('is_active',)

