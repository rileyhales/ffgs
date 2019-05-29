from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .app import Ffgs as App
from .options import wms_colors, geojson_colors


@login_required()
def home(request):
    """
    Controller for the app home page.
    """

    forecasts = SelectInput(
        display_text='Choose a Forecast Model',
        name='colorscheme',
        multiple=False,
        original=True,
        options=[('GFS', 'gfs'), ('WRF', 'wrf')],
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

    colors_geojson = SelectInput(
        display_text='Boundary Colors',
        name='colors_geojson',
        multiple=False,
        original=True,
        options=geojson_colors(),
        initial='#ffffff'
    )

    opacity_geojson = RangeSlider(
        display_text='Boundary Opacity',
        name='opacity_geojson',
        min=.0,
        max=1,
        step=.1,
        initial=.2,
    )

    context = {
        'forecasts': forecasts,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'colors_geojson': colors_geojson,
        'opacity_geojson': opacity_geojson,
        'githublink': App.githublink,
        'version': App.version,
    }

    return render(request, 'ffgs/home.html', context)
