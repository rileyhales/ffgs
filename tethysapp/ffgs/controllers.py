import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .options import *
from .app import Ffgs as App
from .gfsworkflow import run_gfs_workflow
from .wrfprworkflow import run_wrfpr_workflow


@login_required()
def home(request):
    """
    Controller for the app home page.
    """

    gfs_date, wrfpr_date = get_forecastdates()

    ffgsregions = SelectInput(
        display_text='Choose a FFGS Region',
        name='region',
        multiple=False,
        original=True,
        options=ffgs_regions(),
    )

    hisp_models = SelectInput(
        display_text='Choose a Forecast Model',
        name='hisp_models',
        multiple=False,
        original=True,
        options=hispaniola_models(),
    )

    central_models = SelectInput(
        display_text='Choose a Forecast Model',
        name='central_models',
        multiple=False,
        original=True,
        options=centralamerica_models(),
    )

    chartoptions = SelectInput(
        display_text='Choose a Chart Type',
        name='chartoptions',
        multiple=False,
        original=True,
        options=chart_options(),
    )

    resulttypeoptions = SelectInput(
        display_text='Color Regions By Result Type',
        name='resulttype',
        multiple=False,
        original=True,
        options=resulttype_options(),
    )

    colorscheme = SelectInput(
        display_text='Forecast Layer Color Scheme',
        name='colorscheme',
        multiple=False,
        original=True,
        options=wms_colors(),
    )

    opacity_raster = RangeSlider(
        display_text='Forecast Layer Opacity',
        name='opacity_raster',
        min=0,
        max=1,
        step=.05,
        initial=.5,
    )

    legendintervals = RangeSlider(
        display_text='Color Scale Intervals',
        name='legendintervals',
        min=1,
        max=20,
        step=1,
        initial=5,
    )

    context = {
        'gfs_forecastdate': gfs_date,
        'wrfpr_forecastdate': wrfpr_date,
        'hisp_models': hisp_models,
        'central_models': central_models,
        'ffgsregions': ffgsregions,
        'chartoptions': chartoptions,
        'resulttypeoptions': resulttypeoptions,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'legendintervals': legendintervals,
        'githublink': App.githublink,
        'version': App.version,
    }

    return render(request, 'ffgs/home.html', context)


@login_required()
def run_workflows(request):
    """
    The controller for running the workflow to download and process data
    """
    # Check for user permissions here rather than with a decorator so that we can log the failure
    if not User.is_superuser:
        logging.basicConfig(filename=app_settings()['logfile'], filemode='a', level=logging.INFO, format='%(message)s')
        logging.info('A non-superuser tried to run this workflow on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        logging.info('The user was ' + str(request.user))
        return JsonResponse({'Unauthorized User': 'You do not have permission to run the workflow. Ask a superuser.'})

    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # Set the clobber option so that the right folders get deleted/regenerated in the set_environment functions
    if 'clobber' in request.GET:
        clobber = request.GET['clobber'].lower()
        if clobber in ['yes', 'true']:
            logging.info('You chose the clobber option so the timestamps and all the data folders will be overwritten')
            wrksp = App.get_app_workspace().path
            timestamps = os.listdir(wrksp)
            timestamps = [stamp for stamp in timestamps if stamp.endswith('timestamp.txt')]
            for stamp in timestamps:
                with open(os.path.join(wrksp, stamp), 'w') as file:
                    file.write('clobbered')
            logging.info('Clobber complete. Files marked for execution')

    gfs_status = run_gfs_workflow()
    wrf_status = run_wrfpr_workflow()

    return JsonResponse({
        'gfs status': gfs_status,
        'wrf status': wrf_status,
    })
