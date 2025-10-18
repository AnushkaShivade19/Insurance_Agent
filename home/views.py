from django.shortcuts import render

def home_view(request):
    """
    Renders the main homepage for the website.
    """
    return render(request, 'home/homepage.html')