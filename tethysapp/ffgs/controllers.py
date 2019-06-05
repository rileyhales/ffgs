from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

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

    ffgsregions = SelectInput(
        display_text='Choose a FFGS Region',
        name='region',
        multiple=False,
        original=True,
        options=ffgs_regions(),
    )

    models = SelectInput(
        display_text='Choose a Forecast Model',
        name='model',
        multiple=False,
        original=True,
        options=forecastmodels(),
    )

    chartoptions = SelectInput(
        display_text='Choose a Chart Type',
        name='chartoptions',
        multiple=False,
        original=True,
        options=chart_options(),
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
        'chartoptions': chartoptions,
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
    The controller for running the workflow to download and process data
    """
    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # start the workflow by setting the environment
    threddspath, wrksppath, timestamp, redundant = setenvironment()

    # if this has already been done for the most recent forecast, abort the workflow
    if redundant:
        logging.info('\nWorkflow aborted on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        return JsonResponse({'Status': 'Workflow Aborted: already run for most recent data'})

    # run the workflow for each region, for each model in that region
    for region in ffgs_regions():
        logging.info('\nBeginning to process ' + region[1] + ' on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        # download each forecast model, convert them to netcdfs and tiffs
        download_gfs(threddspath, timestamp, region[1])
        gfs_tiffs(threddspath, wrksppath, timestamp, region[1])
        resample(wrksppath, region[1])
        for model in forecastmodels():
            # the geoprocessing functions
            zonal_statistics(wrksppath, timestamp, region[1], model[1])
            nc_georeference(threddspath, timestamp, region[1], model[1])
            # generate color scales and ncml aggregation files
            new_ncml(threddspath, timestamp, region[1], model[1])
            new_colorscales(wrksppath, region[1], model[1])
            set_wmsbounds(threddspath, timestamp, region[1], model[1])
            # cleanup the workspace by removing old files
            cleanup(threddspath, wrksppath, timestamp, region[1], model[1])

    logging.info('\nWorkflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    return JsonResponse({'Status': 'Workflow Completed: normal finish'})
