from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required()
def home(request):
    """
    Controller for the app home page.
    """

    context = {}

    return render(request, 'ffgs/home.html', context)
