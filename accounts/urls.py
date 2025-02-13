from .views import RegisterView, LoginView, vet_dashboard, owner_dashboard, logout_view, profile_view
from django.urls import path

urlpatterns = [
    path('register',RegisterView.as_view(),name='register'),

    path('login',LoginView.as_view(),name='login'),

    path('owner-dashboard',owner_dashboard,name='owner_dashboard'),

    path('vet-dashboard',vet_dashboard,name='vet_dashboard'),

    path('logout',logout_view,name='logout'),

    path('profile',profile_view,name='profile'),
]
