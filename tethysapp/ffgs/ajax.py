import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .options import *
from .newforecasts import *
from .zonal_statistics import *


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_configuration (options)
    """
    return JsonResponse(app_configuration())


def updatedata(request):
    threddspath, timestamp = setenvironment()
    download_gfs(threddspath, timestamp)
    download_wrf(threddspath, timestamp)
    # todo grib to netcdf and nc georeferencing dont work with wrf yet
    for model in forecastmodels():
        grib_to_netcdf(threddspath, timestamp, model[1])
        nc_georeference(threddspath, timestamp, model[1])
        new_ncml(threddspath, timestamp, model[1])
        cleanup(threddspath, timestamp, model[1])
        # set_wmsbounds(threddspath, timestamp, model[1])

    return JsonResponse({'Finished': 'Finished'})
