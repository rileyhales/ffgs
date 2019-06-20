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
        ('Hispaniola', 'hispaniola'),
        ('Central America', 'centralamerica')
    ]


def hispaniola_models():
    """
    Regions that the app currently supports for WRF Puerto Rico
    """
    return [
        ('GFS', 'gfs'),
        ('WRF-PR', 'wrfpr'),
    ]


def centralamerica_models():
    return [
        ('GFS', 'gfs'),
    ]


def chart_options():
    """
    Chart options: cumulative or unique intervals
    """
    return [
        ('6-hr Intervals', 'intervals'),
        ('Cumulative', 'cumulative')
    ]


def get_forecastdates():
    path = os.path.join(App.get_app_workspace().path, 'gfs_timestamp.txt')
    with open(path, 'r') as file:
        time = file.readline()
        if len(time) == 0:
            gfs_date = 'No GFS Timestamp Detected'
        else:
            time = datetime.datetime.strptime(time, "%Y%m%d%H")
            gfs_date = "GFS data from " + time.strftime("%b %d, %I%p UTC")

    path = os.path.join(App.get_app_workspace().path, 'wrfpr_timestamp.txt')
    with open(path, 'r') as file:
        time = file.readline()
        if len(time) == 0:
            wrfpr_date = 'No WRFPR Timestamp Detected'
        else:
            time = datetime.datetime.strptime(time, "%Y%m%d%H")
            wrfpr_date = "WRF-PR data from " + time.strftime("%b %d, %I%p UTC")

    return gfs_date, wrfpr_date
