from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .data_gfs import *
from .ffgsworkflow import *
# from .data_wrf import *


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_configuration (options)
    """
    return JsonResponse(app_configuration())


def updatedata(request):
    threddspath, wrksppath, timestamp = setenvironment()
    for region in ffgs_regions():
        download_gfs(threddspath, timestamp, region[1])
        gfs_24hrfiles(threddspath, wrksppath, timestamp, region[1])
        resample(wrksppath, timestamp, region[1])
        zonal_statistics(wrksppath, timestamp, region[1])
        # download_wrf(threddspath, timestamp)
        for model in forecastmodels():
            nc_georeference(threddspath, timestamp, region[1], model[1])
            new_ncml(threddspath, timestamp, region[1], model[1])
            cleanup(threddspath, timestamp, region[1], model[1])
            set_wmsbounds(threddspath, timestamp, region[1], model[1])

    return JsonResponse({'Finished': 'Finished'})
