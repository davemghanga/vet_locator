from django.db import models
from django.conf import settings
import uuid

class DogProfile(models.Model):
    BREED_CHOICES = [
        ("Africanis", "Africanis"),
        ("German Shepherd", "German Shepherd"),
        ("Labrador Retriever", "Labrador Retriever"),
        ("Golden Retriever", "Golden Retriever"),
        ("Bulldog", "Bulldog"),
        ("Poodle", "Poodle"),
        ("Other", "Other (Specify)")
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=50, choices=BREED_CHOICES)
    custom_breed = models.CharField(max_length=100, blank=True, null=True, help_text="Specify if 'Other' is selected")
    age = models.PositiveIntegerField()
    medical_history = models.TextField(blank=True, null=True, help_text="Add any past medical history, allergies, or treatments.")
    image = models.ImageField(upload_to='dog_profiles/', default='dog_profiles/default.jpeg')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.breed})"
