from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment
from pages.models import DogProfile
from .forms import AppointmentForm
from accounts.models import CustomUser   
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField

@login_required(login_url='login')
def book_appointment(request, vet_id):
    vet = get_object_or_404(CustomUser, id=vet_id, user_type='vet')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                appointment = form.save(commit=False)
                appointment.pet_owner = request.user
                appointment.vet = vet  # Ensure vet is assigned
                
                appointment.full_clean()  # Run model validation
                appointment.save()  # Save after assignment
                
                messages.success(request, 'Your appointment has been booked successfully.')
                return redirect('appointments')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            print(form.errors)  # Print form errors for debugging
    
    else:
        form = AppointmentForm(user=request.user)

    return render(request, 'appointments/book_appointment.html', {
        'form': form, 
        'vet': vet
    })

@login_required(login_url='login')
def view_appointments(request):
    appointments = Appointment.objects.filter(pet_owner=request.user).select_related('vet').annotate(
        status_order=Case(
            When(status='pending', then=Value(1)),
            When(status='confirmed', then=Value(2)),
            When(status='cancelled', then=Value(3)),
            output_field=IntegerField(),
        )
    ).order_by('status_order')  # Order by the custom status order

    return render(request, 'appointments/view_appointments.html', {'appointments': appointments})

@login_required(login_url='login')
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, pet_owner=request.user)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'  # Update the status to cancelled
        appointment.save()
        messages.success(request, 'Your appointment has been cancelled successfully.')
        return redirect('appointments')  # Redirect to the appointments list

    return render(request, 'appointments/cancel_appointment.html', {
        'appointment': appointment,
    })

@login_required(login_url='login')
def vet_appointments(request):
    vet = request.user  # Assuming the user is a vet
    appointments = Appointment.objects.filter(vet=vet).select_related('pet_owner', 'dog')
    return render(request, 'appointments/vet_appointments.html', {'appointments': appointments})

@login_required(login_url='login')
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, vet=request.user)
    if request.method == 'POST':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, 'The appointment has been confirmed.')
        return redirect('vet_appointments')
    return render(request, 'appointments/confirm_appointment.html', {'appointment': appointment})

@login_required(login_url='login')
def complete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, vet=request.user)
    if request.method == 'POST':
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, 'The appointment has been marked as completed.')
        return redirect('vet_appointments')
    return render(request, 'appointments/complete_appointment.html', {'appointment': appointment})

@login_required(login_url='login')
def vet_cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, vet=request.user)
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'The appointment has been cancelled.')
        return redirect('vet_appointments')
    return render(request, 'appointments/vet_cancel_appointment.html', {'appointment': appointment})
