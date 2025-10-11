from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import User, Role

# -----------------------------
# Custom Password Reset Form - SIMPLIFIED
# -----------------------------
class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Return matching active users only"""
        active_users = User._default_manager.filter(
            UserEmail__iexact=email,
            isUserActive=True
        )
        return (u for u in active_users if u.has_usable_password())

# -----------------------------
# Landing Page
# -----------------------------
def landing(request):
    return render(request, "ArcasysApp/landing.html")

# -----------------------------
# Login View - SIMPLIFIED
# -----------------------------
# -----------------------------
# Login View - UPDATED with Remember Me storing password
# -----------------------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.isUserAdmin or request.user.is_superuser:
            return redirect("admin_dashboard")
        else:
            return redirect("add_events")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember_me")

        # Basic validation
        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "ArcasysApp/login.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "ArcasysApp/login.html")

        # Check for pending accounts first
        try:
            pending_user = User.objects.get(UserEmail__iexact=email, isUserActive=False, isUserStaff=True)
            if pending_user.check_password(password):
                messages.warning(request, "Your account is pending administrator approval. Please wait for approval email.")
            else:
                messages.error(request, "Invalid email or password.")
            return render(request, "ArcasysApp/login.html")
        except User.DoesNotExist:
            pass

        # Normal authentication for active users
        user = authenticate(request, UserEmail=email, password=password)

        if user is not None:
            if user.isUserStaff and not user.isUserActive:
                messages.warning(request, "Your account is pending administrator approval. Please wait for approval email.")
                return render(request, "ArcasysApp/login.html")
            
            login(request, user)
            return redirect("events")   # both admin & staff go to events.html
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "ArcasysApp/login.html")

    return render(request, "ArcasysApp/login.html")

# -----------------------------
# Register View - SIMPLIFIED
# -----------------------------
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

# -----------------------------
# Register View - UPDATED with Django's password validation
# -----------------------------
def register_view(request):
    if request.user.is_authenticated:
        if request.user.isUserAdmin or request.user.is_superuser:
            return redirect("admin_dashboard")
        else:
            return redirect("add_events")

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
                messages.error(request, f"{field} is required.")
                return render(request, "ArcasysApp/register.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "ArcasysApp/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "ArcasysApp/register.html")

        # Use Django's built-in password validation (same as password change)
        try:
            validate_password(password)
        except DjangoValidationError as e:
            # Convert Django's validation errors to messages
            for error in e:
                messages.error(request, error)
            return render(request, "ArcasysApp/register.html")

        # Check existing user
        existing_user = User.objects.filter(UserEmail=email).first()
        if existing_user:
            if existing_user.isUserActive:
                messages.error(request, "Email already registered. Please login.")
            else:
                messages.error(request, "Email has pending application. Wait for approval.")
            return render(request, "ArcasysApp/register.html")

        try:
            staff_role = Role.objects.get(RoleName='Staff')
            user = User.objects.create_user(
                UserEmail=email,
                UserFullName=f"{first_name} {last_name}".strip(),
                password=password,
                RoleID=staff_role,
                isUserActive=False,
                isUserStaff=True
            )

            # Send registration email
            html_message = render_to_string('ArcasysApp/registration_notification.html', {'first_name': first_name})
            plain_message = f"""Hello {first_name},

Your staff account has been created successfully and is pending administrator approval.

You will receive another email once your account has been approved.

Best regards,
Marketing Archive Team"""

def events_view(request):
    return render(request, "ArcasysApp/events.html")

def contact_view(request):
    return render(request, "ArcasysApp/contact.html")

def admin_dashboard_view(request):
    return render(request, "ArcasysApp/admin_dashboard.html")

def admin_approval_view(request):
    return render(request, "ArcasysApp/admin_approval.html")
