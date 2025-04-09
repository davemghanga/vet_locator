from django.urls import path
from . import views

urlpatterns = [
    path('book-appointment/<int:vet_id>/', views.book_appointment, name='book_appointment'),  
    path('appointments/', views.view_appointments, name='appointments'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('vet-appointments/', views.vet_appointments, name='vet_appointments'),
    path('vet-appointments/confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('vet-appointments/complete/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
    path('vet-appointments/cancel/<int:appointment_id>/', views.vet_cancel_appointment, name='vet_cancel_appointment'),
    path(
    'appointments/record-visit/<uuid:dog_id>/<int:appointment_id>/',
    views.record_vet_visit,
    name='record_vet_visit'
),

path('rate-vet/<int:appointment_id>/', views.rate_vet, name='rate_vet'),

]