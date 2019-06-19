from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.base import TethysAppBase, url_map_maker

# ROUGHLY IN ORDER OF IMPORTANCE
# todo update the set_wmsbounds function
# todo make the csv of thresholds update automatically like the reservoir app, print the threshold date on the UI
# todo make the wrf model downloads work?
# todo add a clobber option to the workflow so that if clobber is true, delete everything and force a workflow run

"""
GENERAL NOTES
when we add more models, make the setenvironment function create tiff folders for all of them, then make the functions
use the right folder paths based on the model
"""


class Ffgs(TethysAppBase):
    """
    Tethys app class for FFGS Tool.
    """

    name = 'FFGS Tool'
    index = 'ffgs:home'
    icon = 'ffgs/images/ffgs.png'
    package = 'ffgs'
    root_url = 'ffgs'
    color = '#008080'
    description = 'An interface for viewing areas at risk for flood based on the FFGS using the GFS and WRF ' \
                  'forecasts as inputs for determining precipitation depths.'
    tags = ''
    enable_feedback = False
    feedback_emails = []
    githublink = 'https://github.com/rileyhales/ffgs'
    version = '1.1 testing - 19 June 2019'

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)
        url_maps = (
            # url maps for the navigable pages
            UrlMap(
                name='home',
                url='ffgs',
                controller='ffgs.controllers.home'
            ),

            # url maps for data processing functions
            UrlMap(
                name='runGFS',
                url='ffgs/runGFS',
                controller='ffgs.controllers.run_gfs'
            ),
            UrlMap(
                name='runWRFPR',
                url='ffgs/runWRFPR',
                controller='ffgs.controllers.run_wrfpr'
            ),

            # url maps for ajax calls
            UrlMap(
                name='getCustomSettings',
                url='ffgs/ajax/getCustomSettings',
                controller='ffgs.ajax.get_customsettings'
            ),
            UrlMap(
                name='getFloodChart',
                url='ffgs/ajax/getFloodChart',
                controller='ffgs.ajax.get_floodchart'
            ),
            UrlMap(
                name='getCumFloodChart',
                url='ffgs/ajax/getCumFloodChart',
                controller='ffgs.ajax.get_cum_floodchart'
            ),
            UrlMap(
                name='getColorScales',
                url='ffgs/ajax/getColorScales',
                controller='ffgs.ajax.get_colorscales'
            ),
        )
        return url_maps

    def custom_settings(self):
        CustomSettings = (
            CustomSetting(
                name='Local Thredds Folder Path',
                type=CustomSetting.TYPE_STRING,
                description="Local file path to datasets (same as used by Thredds) (e.g. /home/thredds/myDataFolder/)",
                required=True,
            ),
            CustomSetting(
                name='Thredds WMS URL',
                type=CustomSetting.TYPE_STRING,
                description="URL to the FFGS folder on the thredds server (e.g. http://[host]/thredds/ffgs/)",
                required=True,
            ),
        )
        return CustomSettings
