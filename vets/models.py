from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from pages.models import DogProfile
from django.conf import settings

User  = get_user_model()

class AppointmentManager(models.Manager):
    def upcoming(self):
        return self.filter(date__gte=timezone.now()).order_by('date')

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    pet_owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="appointments", 
        limit_choices_to={'user_type': 'owner'}
    )
    vet = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="vet_appointments", 
        limit_choices_to={'user_type': 'vet'}
    )
    dog = models.ForeignKey(
        DogProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="appointments"
    )
    date = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppointmentManager()

    def __str__(self):
        return f"Appointment with Dr. {self.vet.get_full_name()} on {self.date.strftime('%Y-%m-%d %H:%M')}"

def clean(self):
    # Ensure that a vet is assigned only if it is not already set
    if self.pk is None and not self.vet:
        raise ValidationError(_('Vet must be assigned.'))

    # Ensure that a date is provided
    if not self.date:
        raise ValidationError(_('Appointment date is required.'))

    # Check for overlapping appointments
    overlapping_appointments = Appointment.objects.filter(
        vet=self.vet,
        date__range=(self.date - timedelta(hours=1), self.date + timedelta(hours=1))
    ).exclude(pk=self.pk)
    
    if overlapping_appointments.exists():
        raise ValidationError(_('This vet is already booked for the selected time.'))
    

class Rating(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    pet_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vet = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given')
    rating = models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.vet} by {self.pet_owner} - {self.rating} stars"
