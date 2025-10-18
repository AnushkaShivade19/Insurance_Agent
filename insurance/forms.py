from django import forms
from .models import Claim, Policy

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