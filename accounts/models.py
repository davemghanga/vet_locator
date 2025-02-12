from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models

# Create your models here.
class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('owner', 'Pet Owner'),
        ('vet', 'Veterinarian'),
    )

    email = models.EmailField(_('Email Address'),unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='owner')
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    location = models.PointField(geography=True, blank=True, null=True)
    
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'  # Email is the login field
    REQUIRED_FIELDS = []  # No username, only email and password required

    def clean(self):
        """Ensure that vets have first and last names."""
        if self.user_type == 'vet' and (not self.first_name or not self.last_name):
            raise ValidationError("Veterinarians must provide both first and last names.")

    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
