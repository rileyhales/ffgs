import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .options import *
from .manageforecasts import *
from .zonal_statistics import *


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_configuration (options)
    """
    return JsonResponse(app_configuration())


# todo grib to netcdf and nc georeferencing dont work with wrf yet
def updatedata(request):
    threddspath, wrksppath, timestamp = setenvironment()
    for region in ffgs_regions():
        download_gfs(threddspath, timestamp, region[1])
        gfs_24hrfiles(threddspath, wrksppath, timestamp, region[1])
        resample(wrksppath, timestamp, region[1])
        zonal_statistics(wrksppath, timestamp, region[1])
        # download_wrf(threddspath, timestamp)
        for model in forecastmodels():
            grib_to_netcdf(threddspath, timestamp, region[1], model[1])
            nc_georeference(threddspath, timestamp, region[1], model[1])
            new_ncml(threddspath, timestamp, region[1], model[1])
            cleanup(threddspath, timestamp, region[1], model[1])
            # this doesn't work yet
            # set_wmsbounds(threddspath, timestamp, model[1])

    return JsonResponse({'Finished': 'Finished'})
