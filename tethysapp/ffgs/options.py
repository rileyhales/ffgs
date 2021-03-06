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
        'threddsdatadir': App.get_custom_setting("thredds_path"),
        'threddsurl': App.get_custom_setting("thredds_url"),
        'logfile': os.path.join(App.get_app_workspace().path, 'workflow.log')
    }


def wms_colors():
    """
    Color options usable by thredds wms
    """
    return [
        ('Precipitation', 'precipitation'),
        ('Greyscale', 'greyscale'),
        ('Rainbow', 'rainbow'),
        ('OCCAM', 'occam'),
        ('Red-Blue', 'redblue'),
        ('ALG', 'alg'),
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
        ('GFS (6-hr steps, 7 days)', 'gfs'),
        ('WRF-PR (1-hr steps, 2 days)', 'wrfpr'),
    ]


def centralamerica_models():
    return [
        ('GFS (6-hr steps, 7 days)', 'gfs'),
    ]


def chart_options():
    """
    Chart options: cumulative or unique intervals
    """
    return [
        ('Cumulative', 'cumulative'),
        ('Forecast Intervals', 'intervals')
    ]


def resulttype_options():
    """
    Choose to color the regions by the mean, max, or cumulative values
    """
    return [
        ('Cumulative Accumulated Precipitation (mean value each forecast interval)', 'cum_mean'),
        ('Largest Forecast Interval\'s Mean Precipitation (on any 1 Forecast Interval)', 'mean'),
    ]


def get_forecastdates():
    path = os.path.join(App.get_custom_setting('thredds_path'), 'gfs_timestamp.txt')
    if not os.path.isfile(path):
        gfs_date = 'No GFS Timestamp Detected'
    else:
        with open(path, 'r') as file:
            time = file.readline()
            if len(time) == 0:
                gfs_date = 'No GFS Timestamp Detected'
            else:
                time = datetime.datetime.strptime(time, "%Y%m%d%H")
                gfs_date = "GFS data from " + time.strftime("%b %d, %I%p UTC")

    path = os.path.join(App.get_custom_setting('thredds_path'), 'wrfpr_timestamp.txt')
    if not os.path.isfile(path):
        wrfpr_date = 'No WRF-PR Timestamp Detected'
    else:
        with open(path, 'r') as file:
            time = file.readline()
            if len(time) == 0:
                wrfpr_date = 'No WRF-PR Timestamp Detected'
            else:
                time = datetime.datetime.strptime(time, "%Y%m%d%H")
                wrfpr_date = "WRF-PR data from " + time.strftime("%b %d, %I%p UTC")

    return gfs_date, wrfpr_date
