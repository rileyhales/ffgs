from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.base import TethysAppBase, url_map_maker


# ROUGHLY IN ORDER OF IMPORTANCE
# todo create a csv with how many times in the next 10 days each cat_id floods which we use to color the map
# todo decide how to store many days worth of csvs and what naming system to use so the app can read them (append to)
# todo theres a bug in georeferencing the netcdf. it ends up wms-able but not in the right location.

# todo make a dictionary in leaflet.js for setting the right center and zoom of the map
# todo add a control to main.js when you change regions, zoom the map to the new place, swap the geojson and wms layers
# todo check on the setwmsbounds function. make sure it works right. maybe?
# todo make the map move to the region you choose with the select input buttons (see js todo about region geojsons)

# todo make the update workflow a cron job that we can run each day. put a copy of the script in the app
# todo discuss making the csv of thresholds update automatically like the reservoir app does from a google sheet?


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
    version = 'inital dev - 29 May 2019'

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
                name='runWorkflow',
                url='ffgs/runWorkflow',
                controller='ffgs.controllers.run_workflow'
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
