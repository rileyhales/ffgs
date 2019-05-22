from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting


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
    description = 'An interface for viewing areas at risk for flood based on the FFGS'
    tags = ''
    enable_feedback = False
    feedback_emails = []

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

            # url maps for ajax calls
            UrlMap(
                name='getCustomSettings',
                url='ffgs/ajax/getCustomSettings',
                controller='ffgs.ajax.get_customsettings'
            ),

            # url maps for data processing functions
            UrlMap(
                name='updateWRF',
                url='ffgs/data/updateWRF',
                controller='ffgs.tools.process_new_wrf'
            ),
            UrlMap(
                name='updateWRF',
                url='ffgs/data/updateWRF',
                controller='ffgs.tools.process_new_gfs'
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
                description="URL to the GLDAS folder on the thredds server (e.g. http://[host]/thredds/gldas/)",
                required=True,
            ),
            # CustomSetting(
            #     name='Geoserver Workspace URL',
            #     type=CustomSetting.TYPE_STRING,
            #     description="URL (wfs) of the workspace on geoserver (e.g. https://[host]/geoserver/gldas/ows). \n"
            #                 "Enter geojson instead of a url if you experience GeoServer problems.",
            #     required=True,
            # ),
        )
        return CustomSettings
