from django.shortcuts import render

# -----------------------------
# Landing Page View
# -----------------------------
def landing_view(request):
    return render(request, "marketing/landing.html")

# -----------------------------
# Contact Page View
# -----------------------------
def contact_view(request):
    return render(request, "marketing/contact.html")