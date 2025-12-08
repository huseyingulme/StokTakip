from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .utils import log_action


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            log_action(user, 'create', description='Yeni kullanıcı kaydı')
            messages.success(request, 'Kayıt başarılı!')
            return redirect('raporlar:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

