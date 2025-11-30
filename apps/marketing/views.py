from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
import re

logger = logging.getLogger(__name__)


# -----------------------------
# Email Validation Helper Function
# -----------------------------
def is_valid_email(email):
    """
    Strict email validation - only allow specific domains
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False

    domain = email.split('@')[1].lower()

    # ONLY allow these specific domains
    allowed_domains = [
        'gmail.com',
        'yahoo.com',
        'outlook.com',
        'hotmail.com',
        'icloud.com',
        'cit.edu',
    ]

    return domain in allowed_domains


# -----------------------------
# Name Validation Helper Function
# -----------------------------
def is_valid_name(name: str) -> bool:
    """
    Validates that the name:
    - Contains at least one alphabetic character
    - Only allows letters, spaces, hyphens, and apostrophes
    """
    if not name:
        return False
    pattern = re.compile(r"^(?=.*[A-Za-z])[A-Za-z\s'-]+$")
    return bool(pattern.match(name))


# -----------------------------
# Landing Page View
# -----------------------------
def landing_view(request):
    """Landing page that redirects logged-in users to role-based pages"""
    if request.user.is_authenticated:
        return redirect_to_role_based_landing(request.user)

    return render(request, "marketing/landing.html")


# -----------------------------
# Contact Page View - WITH VALIDATION ONLY
# -----------------------------
def contact_view(request):
    """Contact page view - WITH VALIDATION ONLY"""

    if request.method == "POST":
        # Get form data
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        department = (request.POST.get("department") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        message = (request.POST.get("message") or "").strip()

        # Store form data to repopulate on error
        form_data = {
            'full_name': full_name,
            'email': email,
            'department': department,
            'subject': subject,
            'message': message,
        }

        clear_fields = {}
        field_errors = {}

        # FORM VALIDATION IMPLEMENTATION
        # Required fields validation
        if not full_name:
            field_errors['full_name'] = "Please enter your full name."
            clear_fields['full_name'] = True

        if not email:
            field_errors['email'] = "Please enter your email address."
            clear_fields['email'] = True

        if not subject:
            field_errors['subject'] = "Please enter a subject."
            clear_fields['subject'] = True

        if not message:
            field_errors['message'] = "Please enter your message."
            clear_fields['message'] = True

        # Name format validation
        if full_name and not is_valid_name(full_name):
            field_errors['full_name'] = "Please enter a valid name (letters, spaces, hyphens, and apostrophes only)."
            clear_fields['full_name'] = False

        # Email format validation
        if email and not is_valid_email(email):
            field_errors['email'] = "Please enter a valid email address with proper domain (e.g., example@gmail.com)."
            clear_fields['email'] = False

        # If there are validation errors, show them and return
        if field_errors:
            for field, error in field_errors.items():
                messages.error(request, error)
            return render(request, "marketing/contact.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # If validation passes, show success message
        messages.success(request, "Form validation passed! (Email sending will be implemented in next task)")
        logger.info(f"Form validation passed - Name: {full_name}, Email: {email}, Subject: {subject}")

        return render(request, "marketing/contact.html", {
            'form_data': form_data
        })

    # GET request - show empty form
    return render(request, "marketing/contact.html")


# -----------------------------
# Role-Based Redirect Helper
# -----------------------------
def redirect_to_role_based_landing(user):
    """Redirect users to appropriate landing page based on their role"""
    if user.isUserAdmin or user.is_superuser:
        return redirect("events:admin_approval")
    else:
        return redirect("events:events")