"""
Script to download WRF, import into QGIS,and process
© Feb 18, 2019 - Chris Edwards, Jake Lewis, Hunter Williams
Modified for tethys implementation by Riley Hales May 22 2019

WRF Data Information:
URL: https://www.nco.ncep.noaa.gov/pmb/products/hiresw/
Model: AWIPS 3.8km Puerto Rico ARW (NCAR Advanced Research WRF, 2.5km doesn't include the DR) (filename says it's 5km)
Data Access: GRIB2 via urllib
This model runs twice a day, at 6:00 and 18:00. We use the 6:00
We use the 24- and 48-hr accumulated precipitation in kg/m^2
Filename eg: hiresw.t06z.arw_5km.f24.pr.grib2
The variable APCP (Total Precipitation) is stored in Raster Band 282
"""

import os
import shutil
import datetime
import urllib.request
# import qgis.core
from PyQt5.QtCore import QVariant

from .options import app_configuration


def process_new_wrf():
    """
    1. Download today's WRF forecast
    """
    # make a directory for data downloads named wrf_YYMMDD
    threddsdir = app_configuration()['threddsdatadir']
    print(threddsdir)
    today = str(datetime.datetime.now().strftime("%Y%m%d"))
    downloadpath = os.path.join(threddsdir, 'wrf_' + today)
    print('the download path you chose is ' + downloadpath)
    if os.path.exists(downloadpath):
        shutil.rmtree(downloadpath)
        os.mkdir(downloadpath)
    else:
        os.mkdir(downloadpath)

    # download url for the wrf data
    url24 = "https://www.ftp.ncep.noaa.gov/data/nccf/com/hiresw/prod/hiresw." + today + "/hiresw.t06z.arw_5km.f24.pr.grib2"
    gribfile_24 = 'wrf_' + today + '_f24.grib2'
    gribpath_24 = os.path.join(downloadpath, gribfile_24)
    urllib.request.urlretrieve(url24, gribpath_24)
    print(gribfile_24 + " fue descargado (was downloaded).")
    # Download the 48-hr file to the new folder
    url48 = "https://www.ftp.ncep.noaa.gov/data/nccf/com/hiresw/prod/hiresw." + today + "/hiresw.t06z.arw_5km.f48.pr.grib2"
    # 48-hr grib2 filename and path
    gribfile_48 = "wrf_" + today + "_f48.grib2"
    gribpath_48 = os.path.join(downloadpath, gribfile_48)
    # download through url
    urllib.request.urlretrieve(url48, gribpath_48)
    print(gribfile_48 + " fue descargado (was downloaded).")




    # Create Raster Layer
    target_ras_24 = QgsRasterLayer(gribpath_24, gribfile_24)
    # Necessary input for Raster Calculator
    target_24 = QgsRasterCalculatorEntry()
    target_24.raster = target_ras_24
    target_24.bandNumber = 282
    target_24.ref = gribfile_24 + '@282'
    # List of Calculator Entries
    entries = [target_24]
    # 24-hr APCP accumulation Tiff File name and path
    tiff_filename_24 = "WRF-" + today + "_Hr_00-24"
    tiff_path_24 = downloadpath + "/" + tiff_filename_24

    # Raster Calculator. Simply extracting band 282
    calc = QgsRasterCalculator(gribfile_24 + '@282 * 1', tiff_path_24, 'GTiff', target_ras_24.extent(),
                               target_ras_24.width(), target_ras_24.height(), entries)
    calc.processCalculation()

    # Save new raster as a QGIS Layer
    apcp_00to24 = QgsRasterLayer(tiff_path_24, tiff_filename_24)
    # Import the Raster into QGIS
    iface.addRasterLayer(tiff_path_24, tiff_filename_24)
    print(tiff_filename_24 + " fue importado (was imported).")






    # Create Raster Layer
    target_ras_48 = QgsRasterLayer(gribpath_48, gribfile_48)
    # Necessary input for Raster Calculator
    target_48 = QgsRasterCalculatorEntry()
    target_48.raster = target_ras_48
    target_48.bandNumber = 282
    target_48.ref = gribfile_48 + '@282'
    # List of Calculator Entries
    entries = [target_24, target_48]
    # 48-hr APCP accumulation Tiff File name and path
    tiff_filename_48 = "WRF-" + today + "_Hr_24-48"
    tiff_path_48 = downloadpath + "/" + tiff_filename_48

    # *** Raster Calculator:
    # Total 48-hr accumulation subtract the 24-hr accumulation to get the final 24-hr accumulation.
    calc = QgsRasterCalculator(gribfile_48 + '@282 - ' + gribfile_24 + '@282', tiff_path_48, 'GTiff',
                               target_ras_48.extent(), target_ras_48.width(), target_ras_48.height(), entries)
    calc.processCalculation()

    # Save new raster as a QGIS Layer
    apcp_24to48 = QgsRasterLayer(tiff_path_48, tiff_filename_48)
    # Import the Raster into QGIS
    iface.addRasterLayer(tiff_path_48, tiff_filename_48)
    print(tiff_filename_48 + " fue importado (was imported).")

    # *** Zonal Statistics to average Precipitation
    #		(Raster Calculator was done when importing correct band)
    print("Ejecutando estadísticas de zona (Executing Zonal Statistics...)")
    shapefile_path = threddsdir + "/ffgs_wrf_shp/ffgs.shp"
    ffgs_shp = QgsVectorLayer(shapefile_path, 'ffgs', 'ogr')

    zoneStat = QgsZonalStatistics(ffgs_shp, apcp_00to24, '00-24', 1, QgsZonalStatistics.Mean)
    zoneStat.calculateStatistics(None)

    zoneStat = QgsZonalStatistics(ffgs_shp, apcp_24to48, '24-48', 1, QgsZonalStatistics.Mean)
    zoneStat.calculateStatistics(None)

    # *** Add new fields to the shapefile. Example: "Ind_00-24" = Potential to flood, 0-24 hours.
    print("Añadiendo Campo (Adding Field...)")
    layer_provider = ffgs_shp.dataProvider()
    layer_provider.addAttributes([QgsField("Ind_00-24", QVariant.Double),
                                  QgsField("Ind_24-48", QVariant.Double)])
    ffgs_shp.updateFields()

    # *** Calculate fields. Will it flood? FFGS_mm - 0-24Mean = Ind_00-24
    #		Negative means it will flood. Positive means there isn't enought water to flood.
    print("Calculando Atributos (Calculating Attributes...")

    def calculate_attributes():
        with edit(ffgs_shp):
            for feature in ffgs_shp.getFeatures():
                feature.setAttribute(feature.fieldNameIndex('Ind_00-24'), feature['ffgs_mm'] - feature['00-24mean'])
                ffgs_shp.updateFeature(feature)
        with edit(ffgs_shp):
            for feature in ffgs_shp.getFeatures():
                feature.setAttribute(feature.fieldNameIndex('Ind_24-48'), feature['ffgs_mm'] - feature['24-48mean'])
                ffgs_shp.updateFeature(feature)

    calculate_attributes()

    # *** Add Shapefile to the Map
    # iface.addVectorLayer(shapefile_path, "WRF-modificado", 'ogr')

    print("Proceso terminado con éxito (Process successfully finished).")

    return
