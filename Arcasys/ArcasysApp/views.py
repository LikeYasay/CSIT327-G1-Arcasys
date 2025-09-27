from django.shortcuts import render

# Create your views here.
def landing(request):
    return render(request, "ArcasysApp/landing.html")

def login_view(request):
    return render(request, 'ArcasysApp/login.html')

def register_view(request):
    return render(request, 'ArcasysApp/register.html')

def events_view(request):
    return render(request, "ArcasysApp/events.html")

def contact_view(request):
    return render(request, 'ArcasysApp/contact.html')