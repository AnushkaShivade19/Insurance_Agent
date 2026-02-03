from django import forms

from .models import  Policy, InsuranceProduct
from accounts.models import Profile
class PolicyPurchaseForm(forms.ModelForm):
    """
    Form used to finalize the purchase of a new policy.
    """
    # User selects the product they want to enroll in
    product = forms.ModelChoiceField(
        queryset=InsuranceProduct.objects.filter(is_active=True),
        label="Select Recommended Policy"
    )

    class Meta:
        model = Policy
        # Fields the user needs to input to finalize the purchase
        fields = ['product', 'sum_assured', 'start_date']
        widgets = {
            'sum_assured': forms.NumberInput(attrs={'placeholder': 'Enter desired coverage amount (e.g., 200000)'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        
        # Simple validation: Sum Assured must be at least the base premium amount
        if product and cleaned_data.get('sum_assured') is not None and cleaned_data['sum_assured'] < product.base_premium:
            raise forms.ValidationError(f"Sum Assured must be greater than the Base Premium (₹{product.base_premium}).")
        
        return cleaned_data
    
