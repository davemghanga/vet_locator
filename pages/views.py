from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import DogProfile
from .forms import DogProfileForm

@login_required(login_url='login')
def dog_profile_detail(request, id):
    profile = get_object_or_404(DogProfile, id=id, owner=request.user)
    return render(request, 'dog_profiles/details.html', {'profile': profile})

@login_required(login_url='login')
def dog_profile_create(request):
    if request.method == 'POST':
        form = DogProfileForm(request.POST, request.FILES)
        if form.is_valid():
            dog_profile = form.save(commit=False)
            dog_profile.owner = request.user
            dog_profile.save()
            return redirect('owner_dashboard')
    else:
        form = DogProfileForm()
    return render(request, 'dog_profiles/create.html', {'form': form})

@login_required(login_url='login')
def dog_profile_update(request, id):
    profile = get_object_or_404(DogProfile, id=id, owner=request.user)
    if request.method == 'POST':
        form = DogProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dog_profile_detail', id=profile.id)
    else:
        form = DogProfileForm(instance=profile)
    return render(request, 'dog_profiles/update.html', {'form': form})

@login_required(login_url='login')
def dog_profile_delete(request, id):
    profile = get_object_or_404(DogProfile, id=id, owner=request.user)
    if request.method == 'POST':
        profile.delete()
        return redirect('owner_dashboard')
    return render(request, 'dog_profiles/confirm_delete.html', {'profile': profile})
