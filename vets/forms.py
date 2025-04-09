# forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from .models import Appointment
from pages.models import DogProfile
from .models import Rating

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['dog', 'date', 'reason']  # Removed 'vet' from fields
        widgets = {
            'date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'reason': forms.Textarea(
                attrs={
                    'rows': 4,
                    'class': 'form-control'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['dog'].queryset = DogProfile.objects.filter(owner=self.user)
            self.fields['dog'].empty_label = None
        
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Field('dog', css_class='form-control'),
            Field('date'),
            Field('reason'),
            Submit('submit', 'Book Appointment', css_class='btn btn-primary mt-3')
        )

class VetVisitForm(forms.Form):
    diagnosis = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Diagnosis",
        required=True
    )
    treatment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Treatment Given",
        required=True
    )



from django import forms
from .models import Rating

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']

    rating = forms.ChoiceField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.RadioSelect(attrs={'class': 'star-rating'})
    )

