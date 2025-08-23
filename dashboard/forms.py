from django import forms
from accounts.models import CustomUser, InstructorProfile
from dashboard.models import Review
from .models import Tip

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']

class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class AddInstructorDetailsForm(forms.ModelForm):
    class Meta:
        model = InstructorProfile
        fields = ['bio', 'car_type']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'car_type': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TipForm(forms.ModelForm):
    class Meta:
        model = Tip
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tip title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Share your driving tip...'}),
        }