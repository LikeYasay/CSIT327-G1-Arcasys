from django.shortcuts import render

# Basic view - will be filled in later branches
def user_home(request):
    return render(request, 'users/base.html')

# Placeholder for auth views that will be moved from ArcasysApp