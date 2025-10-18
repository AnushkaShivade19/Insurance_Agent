from django import forms

from .models import Claim, Policy, InsuranceProduct, Profile
class ClaimForm(forms.ModelForm):
    """
    Form used by the user to submit a new claim.
    """
    # The 'policy' field needs custom initialization to show only the user's policies
    policy = forms.ModelChoiceField(
        queryset=Policy.objects.none(),  # Default to empty, will be set in __init__
        label="Select Policy to Claim Against"
    )

    class Meta:
        model = Claim
        # We only want users to input the description and amount. 
        # The policy, date, and status will be handled by the view.
        fields = ['policy', 'description', 'claim_amount']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the incident in detail...'}),
            'claim_amount': forms.NumberInput(attrs={'placeholder': 'e.g., 50000.00'})
        }

    def __init__(self, *args, **kwargs):
        # Pop the 'user' object passed from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter the policy choices to include ONLY policies belonging to the current user
        if self.user:
            self.fields['policy'].queryset = Policy.objects.filter(user=self.user, status='ACTIVE')

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
    
class ProfileForm(forms.ModelForm):
    """
    Form for users to update their Profile details.
    We exclude the Aadhar field as it should not be easily changeable via a simple form.
    """
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'date_of_birth']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Village, Mandal, District'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }