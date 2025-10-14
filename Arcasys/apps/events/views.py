from django.shortcuts import render

# Basic view - will be filled in later branches  
def events_home(request):
    return render(request, 'events/base.html')

# Placeholder for event views that will be moved from ArcasysApp