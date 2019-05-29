import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from.options import app_configuration


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_configuration (options)
    """
    return JsonResponse(app_configuration())


def updatedata(request):

    return