from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# -----------------------------
# Landing Page View
# -----------------------------
def landing_view(request):
    """Landing page that redirects logged-in users to role-based pages"""
    # If user is already authenticated, redirect based on role
    if request.user.is_authenticated:
        return redirect_to_role_based_landing(request.user)
    
    # Show regular landing page for non-authenticated users
    return render(request, "marketing/landing.html")

# -----------------------------
# Contact Page View
# -----------------------------
def contact_view(request):
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