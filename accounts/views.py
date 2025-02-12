from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views import View
from django.contrib.auth import authenticate, login
from .forms import LoginForm

# Create your views here.



User = get_user_model()

class RegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")  # Redirect after successful signup


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'users/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Change 'home' to your actual home view
            else:
                form.add_error(None, "Invalid email or password")
        return render(request, 'users/login.html', {'form': form})




