import django
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email 
from django.core.exceptions import ValidationError

def landing(request):
    return render(request, "ArcasysApp/landing.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect("login")

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect("events")   # both admin & user go to events.html
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect("login")

    return render(request, "ArcasysApp/login.html")

def register_view(request):
    if request.method == "POST":
        # Data retrieval
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        # Check for missing fields
        required_fields = {
            'First Name': first_name,
            'Last Name': last_name,
            'Email': email,
            'Password': password,
            'Confirm Password': confirm_password
        }
        
        # Check if any required field is empty
        for name, value in required_fields.items():
            if not value:
                messages.error(request, f"{name} is required.")
                return redirect("register")

        # Check for invalid email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("register")

        # Check for Password Match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        user = User.objects.create_user(
            username=email, 
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        user.save()
        messages.success(request, "Account created!")
        
        return redirect("login")

    return render(request, "ArcasysApp/register.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def events_view(request):
    return render(request, "ArcasysApp/events.html")


def contact_view(request):
    return render(request, "ArcasysApp/contact.html")

def admin_dashboard_view(request):
    return render(request, "ArcasysApp/admin_dashboard.html")