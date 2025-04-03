from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.gis.forms import PointField
from leaflet.forms.widgets import LeafletWidget
from .models import CustomUser
from django.contrib.auth.hashers import make_password  #for hashing
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class CustomUserCreationForm(forms.ModelForm):
    """Form for registering new users (both vets and pet owners)."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    location = PointField(widget=LeafletWidget())

    # Security question fields
    SECURITY_QUESTIONS = [
        ('favorite_teacher', 'What was the name of your favorite teacher?'),
        ('dream_destination', 'What is your dream destination?'),
        ('favorite_food', 'What is your favorite food?'),
    ]

    security_question = forms.ChoiceField(choices=SECURITY_QUESTIONS, label="Security Question")
    security_answer = forms.CharField(max_length=255, label="Security Answer",)  # Mask security answer input

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'user_type', 'location', 'security_question', 'security_answer']

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
        """Save user with hashed password and security answer."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # Hash the security answer before saving
        user.security_answer = make_password(self.cleaned_data["security_answer"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """Form for updating users (used in Django Admin)."""

    password = ReadOnlyPasswordHashField()
    location = PointField(widget=LeafletWidget())

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'user_type', 'location', 'is_active', 'is_staff', 'security_question', 'security_answer']

    def clean_password(self):
        """Return the initial password."""
        return self.initial["password"]


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    """Form for users to update their profile (used in the frontend)."""

    location = PointField(widget=LeafletWidget(), required=False)  # Make location optional

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'location',]



class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput,
        required=True,
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        required=True,
        validators=[validate_password],  # Validate the new password
    )
    confirm_new_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput,
        required=True,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user  # Store the logged-in user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """Validate the current password."""
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise ValidationError("The current password is incorrect.")
        return current_password

    def clean(self):
        """Ensure the new passwords match."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValidationError("The new passwords do not match.")
        return cleaned_data