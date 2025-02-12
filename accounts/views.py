from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth import get_user_model, authenticate, login
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Import Django messages
from .forms import LoginForm, CustomUserCreationForm

User = get_user_model()

class RegisterView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("login")  # Redirect after successful signup

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Registration successful! You can now log in.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Registration failed. Please correct the errors below.")
        return super().form_invalid(form)


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                if user.user_type == "vet":
                    return redirect(reverse_lazy("vet_dashboard"))
                return redirect(reverse_lazy("owner_dashboard"))
            else:
                messages.error(request, "Invalid email or password.")
        return render(request, 'accounts/login.html', {'form': form})


# Dashboard Views
@login_required
def vet_dashboard(request):
    return render(request, "accounts/vet_dashboard.html")


@login_required
def owner_dashboard(request):
    return render(request, "accounts/owner_dashboard.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect(reverse_lazy('login'))

