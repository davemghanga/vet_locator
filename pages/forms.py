from django import forms
from .models import DogProfile

class DogProfileForm(forms.ModelForm):
    class Meta:
        model = DogProfile
        fields = ['name', 'breed', 'custom_breed', 'age', 'medical_history', 'image']
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        breed = cleaned_data.get("breed")
        custom_breed = cleaned_data.get("custom_breed")

        if breed == "Other" and not custom_breed:
            self.add_error('custom_breed', "Please specify the breed if 'Other' is selected.")

        return cleaned_data
