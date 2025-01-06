from django.contrib.auth.models import User
from django import forms
from .models import Orders, UserProfile

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'required': True,
                'placeholder': 'Masukkan username...',
                'title': 'Maksimal 150 huruf. Hanya huruf, angka dan @/./+/-/_'}),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Masukkan email.',
                'title': 'Masukkan email yang valid.'  # Optional: Tooltip
            }),
        }
        help_texts = {
            'username': None,  # Completely hide the default help text
        }
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'required': True,
                'placeholder': 'Masukkan nomor telepon',
                'title': 'No. telepon minimal 10 digit.',
            }),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError("No. telepon hanya bisa menyimpan angka.")
        if len(phone_number) < 10:
            raise forms.ValidationError("No. telepon minimal 10 digit.")
        return phone_number

class ReceiptUploadForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ['receipt_image']  # Include only the receipt image field
