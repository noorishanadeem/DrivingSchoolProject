from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser, InstructorProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = InstructorProfile
        fields = ['bio', 'car_type']

        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'car_type': forms.TextInput(attrs={'class': 'form-control'}),
        }