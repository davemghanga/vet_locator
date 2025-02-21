from django.urls import path
from . import views

urlpatterns = [
    path('',views.recommend_solution,name='recommend_solution'),


]
