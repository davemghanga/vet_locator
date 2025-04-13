from django.urls import path
from . import views

urlpatterns = [
    path('dogs/<uuid:id>/', views.dog_profile_detail, name='dog_profile_detail'),
    path('dogs/create/', views.dog_profile_create, name='dog_profile_create'),
    path('dogs/<uuid:id>/update/', views.dog_profile_update, name='dog_profile_update'),
    path('dogs/<uuid:id>/delete/', views.dog_profile_delete, name='dog_profile_delete'),

    #find_vets
    path('vets/find-vet/',views.find_vets,name='find_vets'),

    #vet details
    path('vet/<int:vet_id>/', views.vet_details, name='vet_details'),

    path('contact/', views.contact_view, name='contact'),

  path('services/', views.services, name='services'),


   path('vet/<int:vet_id>/reviews/', views.vet_reviews, name='vet_reviews'),




]