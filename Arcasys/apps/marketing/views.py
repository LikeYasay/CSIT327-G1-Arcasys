from django.shortcuts import render

# Basic view - will be filled in later branches
def marketing_home(request):
    return render(request, 'marketing/base.html')

# Placeholder for landing/contact views that will be moved from ArcasysApp