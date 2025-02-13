from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.gis.forms import PointField
from leaflet.forms.widgets import LeafletWidget
from .models import CustomUser

class CustomUserCreationForm(forms.ModelForm):
    """Form for registering new users (both vets and pet owners)."""
    
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    location = PointField(widget=LeafletWidget())

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'user_type', 'location']

    def clean_password2(self):
        """Ensure both passwords match."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def clean(self):
        """Ensure vets provide first and last names."""
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if user_type == "vet" and (not first_name or not last_name):
            raise forms.ValidationError("Veterinarians must provide both first and last names.")

    def save(self, commit=True):
        """Save user with hashed password."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """Form for updating users (used in Django Admin)."""
    
    password = ReadOnlyPasswordHashField()
    location = PointField(widget=LeafletWidget())

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'user_type', 'location', 'is_active', 'is_staff']

    def clean_password(self):
        """Return the initial password."""
        return self.initial["password"]


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)