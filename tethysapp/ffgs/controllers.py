from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .app import Ffgs as App
from .data_gfs import *
# from .data_wrf import *
from .ffgsworkflow import *
from .options import wms_colors, forecastmodels, ffgs_regions, get_forecastdate


@login_required()
def home(request):
    """
    Controller for the app home page.
    """

    forecastdate = get_forecastdate()

    models = SelectInput(
        display_text='Choose a Forecast Model',
        name='model',
        multiple=False,
        original=True,
        options=forecastmodels(),
    )

    ffgsregions = SelectInput(
        display_text='Choose a FFGS Region',
        name='region',
        multiple=False,
        original=True,
        options=ffgs_regions(),
    )

    colorscheme = SelectInput(
        display_text='Raster Color Scheme',
        name='colorscheme',
        multiple=False,
        original=True,
        options=wms_colors(),
        initial='rainbow'
    )

    opacity_raster = RangeSlider(
        display_text='Raster Opacity',
        name='opacity_raster',
        min=.5,
        max=1,
        step=.05,
        initial=1,
    )

    opacity_geojson = RangeSlider(
        display_text='FFGS Watershed Opacity',
        name='opacity_ffgs',
        min=.0,
        max=1,
        step=.1,
        initial=.8,
    )

    context = {
        'forecastdate': forecastdate,
        'models': models,
        'ffgsregions': ffgsregions,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'opacity_geojson': opacity_geojson,
        'githublink': App.githublink,
        'version': App.version,
    }

    return render(request, 'ffgs/home.html', context)


@login_required()
def run_workflow(request):
    """
    The controller for running the workflow to download and .
    """
    logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')

    # todo add a check here to see if you've already run the workflow for this day
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
            cleanup(threddspath, wrksppath, timestamp, region[1], model[1])
            set_wmsbounds(threddspath, timestamp, region[1], model[1])

    return JsonResponse({'Status': 'Workflow Completed Successfully'})
