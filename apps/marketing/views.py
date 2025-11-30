from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


# -----------------------------
# Landing Page View
# -----------------------------
def landing_view(request):
    """Landing page that redirects logged-in users to role-based pages"""
    if request.user.is_authenticated:
        return redirect_to_role_based_landing(request.user)

    return render(request, "marketing/landing.html")


# -----------------------------
# Contact Page View - BASIC FORM FUNCTIONALITY ONLY
# -----------------------------
def contact_view(request):
    """Contact page view - BASIC FORM FUNCTIONALITY ONLY"""

    if request.method == "POST":
        # Get form data - NO VALIDATION YET
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        department = (request.POST.get("department") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        message = (request.POST.get("message") or "").strip()

        # BASIC form data persistence
        form_data = {
            'full_name': full_name,
            'email': email,
            'department': department,
            'subject': subject,
            'message': message,
        }

        # Just show the form data for now - NO EMAIL SENDING YET
        messages.info(request,
                      "Form received successfully! (Validation and email sending will be implemented in next tasks)")
        logger.info(f"Form submitted - Name: {full_name}, Email: {email}, Subject: {subject}")

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