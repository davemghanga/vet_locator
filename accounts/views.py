from django.shortcuts import render, redirect
from django.contrib.auth import logout, get_user_model, authenticate, login
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, CustomUserCreationForm, UserProfileForm
from geopy.geocoders import Nominatim
from django.contrib.auth.hashers import check_password
from pages.models import DogProfile


from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.cache import cache
from .models import CustomUser   # Make sure to import your CustomUser  model
from .forms import CustomUserCreationForm  # Import your custom user creation form

import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import SetPasswordForm

class RegisterView(CreateView):
    model = CustomUser   # Use your CustomUser  model
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        # Call the parent form_valid method to create the user
        response = super().form_valid(form)

        # Check if the user is a vet and clear the cache
        if form.cleaned_data.get('user_type') == 'vet':
            # Extract the location from the PointField
            location = self.object.location  # This is the PointField
            if location:
                lat = location.y  # Latitude
                lon = location.x  # Longitude
                cache_key = f"vets_near_{lat}_{lon}"
                cache.delete(cache_key)  # Clear the cache for the relevant coordinates

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

    

@login_required(login_url='login')
def vet_dashboard(request):
    return render(request, "accounts/vet_dashboard.html")

@login_required(login_url='login')
def owner_dashboard(request):
    profiles = DogProfile.objects.filter(owner=request.user)
    return render(request, "accounts/owner_dashboard.html", {"profiles": profiles})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect(reverse_lazy(''))

def get_location_name(coordinates):
    geolocator = Nominatim(user_agent="vet_locator")
    try:
        location = geolocator.reverse(coordinates, exactly_one=True)
        return location.address if location else "Unknown Location"
    except Exception:
        return "Unknown Location"

@login_required(login_url='login')
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

@login_required(login_url='login')
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to profile page after saving
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'accounts/edit_profile.html', {'form': form})




@login_required(login_url='login')
def delete_profile(request):
    if request.method == "POST":
        password = request.POST.get("password")
        # Verify the password
        if not check_password(password, request.user.password):
            messages.error(request, "Incorrect password. Account not deleted.")
            return redirect("delete_profile")

        user_email = request.user.email  # Save email for message
        request.user.delete()  # Delete the user
        logout(request)  # Log out the user
        messages.success(request, f"Your account ({user_email}) has been deleted successfully.")
        return redirect("register")  # Redirect to register or home page

    return render(request, "accounts/delete_profile.html")



def generate_reset_code(length=6):
    """Generate a random password reset code."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            # Generate a reset code
            reset_code = generate_reset_code()
            # Save the reset code in the session
            request.session['reset_code'] = reset_code
            request.session['user_id'] = user.id
            
            # Send email with the reset code
            subject = "Password Reset Code"
            message = f"Your password reset code is: {reset_code}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            
            messages.success(request, "A password reset code has been sent to your email.")
            return redirect('password_reset_confirm')
        except CustomUser.DoesNotExist:
            messages.error(request, "No user is associated with this email address.")
    return render(request, 'accounts/password_reset_request.html')


def password_reset_confirm(request):
    if request.method == "POST":
        entered_code = request.POST.get("code")
        new_password = request.POST.get("new_password")
        
        # Check if the entered code matches the one in the session
        if entered_code == request.session.get('reset_code'):
            user_id = request.session.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            form = SetPasswordForm(user, {'new_password': new_password})
            if form.is_valid():
                user = form.save()
                messages.success(request, "Your password has been set. You can now log in.")
                return redirect('login')
        else:
            messages.error(request, "The reset code is invalid.")
    
    return render(request, 'accounts/password_reset_confirm.html')

