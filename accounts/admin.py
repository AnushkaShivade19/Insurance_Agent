from django.contrib import admin
from .models import Profile,Agent

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'is_kyc_verified')
    search_fields = ('user__username', 'phone_number')

@admin.register(Agent)
class InsuranceAgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone_number', 'rating', 'is_verified')
    search_fields = ('name', 'location', 'languages')
    list_filter = ('is_verified', 'location')