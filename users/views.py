from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()


def register_view(request):
    """Ro'yxatdan o'tish"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Oddiy tekshiruvlar
        if password1 != password2:
            messages.error(request, "Parollar mos kelmadi!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu username allaqachon band!")
            return redirect('register')

        # Foydalanuvchi yaratish
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        login(request, user)
        messages.success(request, f"Xush kelibsiz, {username}!")
        return redirect('courses:course_list')

    return render(request, 'users/register.html')


def login_view(request):
    """Tizimga kirish"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {username}!")
            next_url = request.GET.get('next', 'courses:course_list')
            return redirect(next_url)
        else:
            messages.error(request, "Username yoki parol xato!")

    return render(request, 'users/login.html')


def logout_view(request):
    """Tizimdan chiqish"""
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz")
    return redirect('courses:course_list')