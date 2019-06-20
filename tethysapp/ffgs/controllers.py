import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .app import Ffgs as App
from .gfsworkflow import run_gfs_workflow
from .options import *
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
        min=0,
        max=1,
        step=.05,
        initial=.5,
    )

    context = {
        'gfs_forecastdate': gfs_date,
        'wrfpr_forecastdate': wrfpr_date,
        'hisp_models': hisp_models,
        'central_models': central_models,
        'ffgsregions': ffgsregions,
        'chartoptions': chartoptions,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'githublink': App.githublink,
        'version': App.version,
    }

    return render(request, 'ffgs/home.html', context)


@login_required()
def run_workflows(request):
    """
    The controller for running the workflow to download and process data
    """
    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # todo make the workflows handle http errors better???
    gfs_status = run_gfs_workflow()
    wrf_status = run_wrfpr_workflow()

    return JsonResponse({
        'gfs status': gfs_status,
        'wrf status': wrf_status,
    })
