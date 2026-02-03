from django import forms
from .models import Claim
from insurance.models import Policy

class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['policy', 'claim_amount', 'evidence_image', 'description']
        widgets = {
            'policy': forms.Select(attrs={'class': 'form-control'}),
            'claim_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50000'}),
            'evidence_image': forms.FileInput(attrs={'class': 'form-control-file'}),
            # CRITICAL: We add id='voiceInput' so JS can find this box
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'id': 'voiceInput', 
                'placeholder': 'Tap the mic and speak...'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ClaimForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['policy'].queryset = Policy.objects.filter(user=user, status='ACTIVE')
            self.fields['policy'].empty_label = "Select Your Policy"