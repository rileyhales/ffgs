from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .options import *
from .app import Ffgs as App


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
