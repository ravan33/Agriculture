"""
Forms for the core application.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, Query, Advice, AIDisease, InventoryItem, Rating


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with additional fields.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your last name'
        })
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your phone number (optional)'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your address (optional)',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 
                 'phone_number', 'address', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.address = self.cleaned_data.get('address', '')
        user.is_active = False  # Require admin activation
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with styled widgets.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter your password'
        })
    )


class QueryForm(forms.ModelForm):
    """
    Form for farmers to submit queries.
    """
    class Meta:
        model = Query
        fields = ['title', 'description', 'crop_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Brief description of your crop issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Describe the symptoms and any relevant details...',
                'rows': 5
            }),
            'crop_image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'accept': 'image/*'
            })
        }


class AdviceForm(forms.ModelForm):
    """
    Form for experts to provide advice.
    """
    class Meta:
        model = Advice
        fields = ['content', 'confidence_level']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Provide your expert advice and recommendations...',
                'rows': 8
            }),
            'confidence_level': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            })
        }


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their profile information.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'city']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Enter your city for weather updates'
            })
        }


class AIDiagnosisForm(forms.ModelForm):
    """
    Form for AI disease diagnosis.
    """
    class Meta:
        model = AIDisease
        fields = ['crop_image']
        widgets = {
            'crop_image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'accept': 'image/*'
            })
        }


class InventoryItemForm(forms.ModelForm):
    """
    Form for adding/updating inventory items.
    """
    class Meta:
        model = InventoryItem
        fields = ['name', 'quantity', 'unit', 'category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Enter item name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Enter quantity',
                'step': '0.01'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'e.g., kg, liters, bags'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            })
        }


class RatingForm(forms.ModelForm):
    """
    Form for rating expert advice.
    """
    class Meta:
        model = Rating
        fields = ['score', 'comment']
        widgets = {
            'score': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Optional: Share your feedback about this advice'
            })
        }
