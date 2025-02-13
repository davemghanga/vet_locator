from django.shortcuts import render, redirect
from django.contrib.auth import logout, get_user_model, authenticate, login
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, CustomUserCreationForm
from geopy.geocoders import Nominatim

User = get_user_model()

class RegisterView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("login")

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
                return redirect(reverse_lazy("vet_dashboard") if user.user_type == "vet" else reverse_lazy("owner_dashboard"))
            else:
                messages.error(request, "Invalid email or password.")
        return render(request, 'accounts/login.html', {'form': form})

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

def get_location_name(coordinates):
    geolocator = Nominatim(user_agent="vet_locator")
    try:
        location = geolocator.reverse(coordinates, exactly_one=True)
        return location.address if location else "Unknown Location"
    except Exception:
        return "Unknown Location"

@login_required
def profile_view(request):
    user = request.user
    location_name = "Unknown Location"

    if user.location:
        try:
            # Convert the POINT(x y) format to lat, lon
            location_str = str(user.location).replace("POINT(", "").replace(")", "")
            lon, lat = map(float, location_str.split())
            location_name = get_location_name((lat, lon))
        except ValueError:
            location_name = "Invalid location data."

    return render(request, "accounts/profile_details.html", {"location_name": location_name})