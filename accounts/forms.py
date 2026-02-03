from django import forms
from django.contrib.auth.models import User
from .models import Profile
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
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class OnboardingForm(forms.ModelForm):
    """
    The 'User Friendly' form displayed after login if profile is incomplete.
    """
    class Meta:
        model = Profile
        fields = ['phone_number', 'date_of_birth', 'gender', 'address', 'city', 'state', 'pincode']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Mobile Number'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'House No, Street Area'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
        }