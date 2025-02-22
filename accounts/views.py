from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, CustomUserCreationForm, UserProfileForm
from geopy.geocoders import Nominatim
from django.contrib.auth.hashers import check_password, make_password
from pages.models import DogProfile
from .models import CustomUser
from .forms import PasswordChangeForm


class RegisterView(CreateView):
    model = CustomUser
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


@login_required(login_url='login')
def vet_dashboard(request):
    return render(request, "accounts/vet_dashboard.html")


@login_required(login_url='login')
def owner_dashboard(request):
    profiles = DogProfile.objects.filter(owner=request.user)
    return render(request, "accounts/owner_dashboard.html", {"profiles": profiles})


@login_required(login_url='login')
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
        if not check_password(password, request.user.password):
            messages.error(request, "Incorrect password. Account not deleted.")
            return redirect("delete_profile")

        user_email = request.user.email  # Save email for message
        request.user.delete()  # Delete the user
        logout(request)  # Log out the user
        messages.success(request, f"Your account ({user_email}) has been deleted successfully.")
        return redirect("register")  # Redirect to register or home page


def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")  # Get the email from the form
        security_question = request.POST.get("security_question")  # Get the security question from the form
        security_answer = request.POST.get("security_answer")  # Get the security answer from the form

        # Rate limiting: Check if the user has exceeded the maximum attempts
        reset_attempts = request.session.get('reset_attempts', 0)
        if reset_attempts >= 3:
            messages.error(request, "Too many attempts. Please try again later.")
            return redirect('password_reset_request')

        try:
            # Attempt to find the user based on the email
            user = CustomUser.objects.get(email=email)

            # Check if the security question and answer match
            if (user.security_question == security_question and
                    check_password(security_answer, user.security_answer)):
                request.session['reset_attempts'] = 0  # Reset attempts on success
                return redirect('password_reset_confirm', user_id=user.id)
            else:
                request.session['reset_attempts'] = reset_attempts + 1
                messages.error(request, "Invalid security question or answer.")
                return redirect('password_reset_request')

        except CustomUser.DoesNotExist:
            messages.error(request, "No account is associated with this email address.")
            return redirect('password_reset_request')

    # If GET request, render the form to enter email, security question, and security answer
    return render(request, 'accounts/password_reset_request.html')


def password_reset_confirm(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Check if the new password and confirm password match
        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Your password has been reset successfully. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "The passwords do not match.")
            return redirect('password_reset_confirm', user_id=user.id)

    return render(request, 'accounts/password_reset_confirm.html', {'user': user})


@login_required(login_url='login')
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            # Set the new password
            new_password = form.cleaned_data["new_password"]
            request.user.set_password(new_password)
            request.user.save()

            # Log the user back in (since their session is invalidated after password change)
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)

            messages.success(request, "Your password has been changed successfully.")
            return redirect("profile")  # Redirect to the user's profile or dashboard
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/password_change.html", {"form": form})