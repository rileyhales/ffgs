from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .app import Ffgs as App
# from .data_wrf import *
from .gfsworkflow import run_gfs_workflow
from .wrfprworkflow import run_wrfpr_workflow

from .options import wms_colors, forecastmodels, ffgs_regions, get_forecastdate, chart_options


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
        min=0,
        max=1,
        step=.05,
        initial=.5,
    )

    context = {
        'forecastdate': forecastdate,
        'models': models,
        'ffgsregions': ffgsregions,
        'chartoptions': chartoptions,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'githublink': App.githublink,
        'version': App.version,
    }

    return render(request, 'ffgs/home.html', context)


@login_required()
def run_gfs(request):
    """
    The controller for running the workflow to download and process data
    """
    gfs_status = run_gfs_workflow()

    return JsonResponse({
        'gfs status': gfs_status,
    })

@login_required()
def run_wrfpr(request):
    """
    The controller for running the workflow to download and process data
    """
    wrf_status = run_wrfpr_workflow()

    return JsonResponse({
        'wrf status': wrf_status,
    })