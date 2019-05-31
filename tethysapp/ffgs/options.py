import datetime
import os

from .app import Ffgs as App


def app_settings():
    """
    Gets the settings for the app for use in other functions and ajax for leaflet
    Dependencies: os, App (app)
    """
    return {
        'app_wksp_path': os.path.join(App.get_app_workspace().path, ''),
        'threddsdatadir': App.get_custom_setting("Local Thredds Folder Path"),
        'threddsurl': App.get_custom_setting("Thredds WMS URL"),
        'logfile': os.path.join(App.get_app_workspace().path, 'workflow.log')
    }


def wms_colors():
    """
    Color options usable by thredds wms
    """
    return [
        ('SST-36', 'sst_36'),
        ('Greyscale', 'greyscale'),
        ('Rainbow', 'rainbow'),
        ('OCCAM', 'occam'),
        ('OCCAM Pastel', 'occam_pastel-30'),
        ('Red-Blue', 'redblue'),
        ('NetCDF Viewer', 'ncview'),
        ('ALG', 'alg'),
        ('ALG 2', 'alg2'),
        ('Ferret', 'ferret'),
        ]


def ffgs_regions():
    """
    FFGS regions that the app currently supports
    """
    return [
        ('Hispaniola', 'hispaniola')
    ]


def forecastmodels():
    return [
        ('GFS', 'gfs'),
        # ('WRF', 'wrf'),
    ]


def get_forecastdate():
    path = os.path.join(App.get_app_workspace().path, 'timestep.txt')
    with open(path, 'r') as file:
        time = file.readline()
        time = datetime.datetime.strptime(time, "%Y%m%d%H")
        return "This GFS data from " + time.strftime("%b %d, %I%p UTC")
