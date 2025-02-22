from . import views
from django.urls import path

urlpatterns = [
    path('register',views.RegisterView.as_view(),name='register'),

    path('login',views.LoginView.as_view(),name='login'),

    path('owner-dashboard',views.owner_dashboard,name='owner_dashboard'),

    path('vet-dashboard',views.vet_dashboard,name='vet_dashboard'),

    path('logout',views.logout_view,name='logout'),

    path('profile',views.profile_view,name='profile'),

    path('user-profile',views.edit_profile,name='edit_profile'),

    path('delete-profile',views.delete_profile,name='delete_profile'),

    path('password_reset/', views.password_reset_request, name='password_reset_request'),

    path('password_reset_confirm/<int:user_id>/', views.password_reset_confirm, name='password_reset_confirm'),

    path("password_change/", views.password_change, name='password_change'),

]
