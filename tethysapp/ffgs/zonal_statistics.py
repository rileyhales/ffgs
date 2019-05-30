import os
import shutil
import datetime
import urllib.request
import numpy
import pandas as pd
import rasterio
from rasterio.enums import Resampling
import rasterstats
import pprint

from .options import *

def get_region():
    """
    Script to determine region of interest    Not Sure the best way to do this
    :return:
    """
    region = 'Hispaniola'

    return region


def download_gfs():
    """
    Script for downloading the GFS Precipitation forecast for the next 10-days in grib format.
    Dependencies: os, shutil, datetime, urllib.request
    :return: filepath where files were downloaded
    """

    # Specify the directory where the gfs files will be saved
    threddsdir = app_configuration()['threddsdatadir']
    print('Thredds Directory = ' + threddsdir)
    today = datetime.datetime.utcnow()
    today_str = today.strftime("%Y%m%d")
    gfs_folder = os.path.join(threddsdir, 'gfs_' + today_str + '_00')
    print('Download Path = ' + gfs_folder)

    # Create a directory for the newest forecast
    if os.path.exists(gfs_folder):
        print('Path already exists and will be deleted.')
        shutil.rmtree(gfs_folder)
        os.mkdir(gfs_folder)
    else:
        os.mkdir(gfs_folder)

    # List of the desired GFS file extensions (f006, f012, etc.)
    # file_id_list = ["006", "012", "018", "024"]   # Shortened for Testing
    file_id_list = ["006", "012", "018", "024", "030", "036", "042", "048",
                    "054", "060", "066", "072", "078", "084", "090", "096",
                    "102", "108", "114", "120", "126", "132", "138", "144",
                    "150", "156", "162", "168", "174", "180", "186", "192",
                    "198", "204", "210", "216", "222", "228", "234", "240"
                    ]   # 10-days of 6-hr accumulated precipitation


    # Loop to download and import rasters from the NOMADS database, GFS 0.25 Degree
    for i in range(len(file_id_list)):

        # Specify the URL to download GFS for various regions:

        # No Subregion, Lat 0 to 360
        # data_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t00z.pgrb2.0p25.f" + file_id_list[
        #     i] + "&all_lev=on&var_APCP=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fgfs." + today_str + "00"

        # Whole Globe, Lat -180 to 180
        # data_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t00z.pgrb2.0p25.f" + file_id_list[
        #     i] + "&all_lev=on&var_APCP=on&subregion=&leftlon=-180&rightlon=180&toplat=90&bottomlat=-90&dir=%2Fgfs." + today_str + "00"

        # Dominican Republic & Haiti (Hispaniola)
        data_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t00z.pgrb2.0p25.f" + file_id_list[
            i] + "&all_lev=on&var_APCP=on&subregion=&leftlon=-75&rightlon=-68&toplat=20&bottomlat=17&dir=%2Fgfs." + today_str + "00"


        # Specify the filepath and download the files
        filename = "gfs_apcp_" + today_str + "_t00_f" + file_id_list[i] + ".grib"
        download_file_path = gfs_folder + "/" + filename
        urllib.request.urlretrieve(data_url, download_file_path)
        print("'" + filename + "' was downloaded.")

    return gfs_folder


def daily_gfs_precip(gfs_folder):
    """
    Script to combine 6-hr accumulation grib files into 24-hr accumulation geotiffs.
    Dependencies: os, datetime, numpy, rasterio
    :param gfs_folder: folder where grib files were downloaded
    :return: folder with daily precipitaion geotiffs
    """

    today = datetime.datetime.utcnow()
    today_str = today.strftime("%Y%m%d")

    # Create directory for the 24-hr files
    daily_folder = os.path.join(gfs_folder, '24_hr_GeoTIFFs')
    if os.path.exists(daily_folder):
        shutil.rmtree(daily_folder)
        os.mkdir(daily_folder)
    else:
        os.mkdir(daily_folder)

    # List all 40 grib files
    grib_list = []
    for i in os.listdir(gfs_folder):
        if i[-4:] == 'grib':
            grib_list.append(os.path.join(gfs_folder, i))
    grib_list.sort()

    # Split list into lists of 4 files
    n = 4
    daily_file_list = [grib_list[j*n:(j+1)*n] for j in range((len(grib_list) + n -1)//n)]

    # Read raster dimensions
    raster_dim = rasterio.open(daily_file_list[0][0])
    width = raster_dim.width
    height = raster_dim.height
    lon_min = raster_dim.bounds.left
    lon_max = raster_dim.bounds.right
    lat_min = raster_dim.bounds.bottom
    lat_max = raster_dim.bounds.top

    # Geotransform for each 24-hr raster (east, south, west, north, width, height)
    geotransform = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width, height)

    # Add rasters together to form 24-hr raster
    for i in daily_file_list:

        daily_array = numpy.zeros((height, width))

        # Copy raster to 2D Array and add to Daliy Array
        for j in range(len(i)):
            file = i[j]
            src = rasterio.open(file)
            six_hr_array = src.read(1)
            daily_array = daily_array + six_hr_array

        # Specify the filepath for the 24-hr raster
        last_hr = int(i[-1][-8:-5])
        start_hr = str(last_hr-24).rjust(3,'0')
        end_hr = str(last_hr).rjust(3,'0')
        daily_filename = 'gfs_apcp_' + today_str + '_hrs' + start_hr + '-' + end_hr + '.tif'
        daily_filepath = os.path.join(daily_folder,daily_filename)

        # Save the 24-hr raster
        with rasterio.open(
                daily_filepath,
                'w',
                driver='GTiff',
                height=daily_array.shape[0],
                width=daily_array.shape[1],
                count=1,
                dtype=daily_array.dtype,
                nodata=numpy.nan,
                crs='+proj=latlong',
                transform=geotransform,
        ) as dst:
            dst.write(daily_array, 1)

    return daily_folder


def resample(gfs_folder, daily_folder):
    """
    Script to resample rasters from .25 o .0025 degree in order for rasterstats to work
    :param gfs_folder: folder of raw grib data and other new directories
    :param daily_folder: folder of 24-hr GeoTIFFs
    :return: resample_folder: folder of 24-hr resampled GeoTIFFs
    """
    # Create directory for the resampled GeoTIFFs
    today = datetime.datetime.utcnow()
    today_str = today.strftime("%Y%m%d")
    resample_folder = os.path.join(gfs_folder, '24_hr_GeoTIFFs_resampled')
    if os.path.exists(resample_folder):
        print('Path already exists and will be deleted.')
        shutil.rmtree(resample_folder)
        os.mkdir(resample_folder)
    else:
        os.mkdir(resample_folder)

    # List all 10 GeoTIFFs
    tif_list = []
    for i in os.listdir(daily_folder):
        if i[-3:] == 'tif':
            tif_list.append(os.path.join(daily_folder, i))
    tif_list.sort()
    # pprint.pprint(tif_list)

    # Read raster dimensions
    raster_dim = rasterio.open(tif_list[0])
    width = raster_dim.width
    height = raster_dim.height
    lon_min = raster_dim.bounds.left
    lon_max = raster_dim.bounds.right
    lat_min = raster_dim.bounds.bottom
    lat_max = raster_dim.bounds.top

    # Geotransform for each 24-hr resampled raster (east, south, west, north, width, height)
    geotransform_res = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width * 100, height * 100)

    # Resample each GeoTIFF
    for file in tif_list:
        with rasterio.open(file) as dataset:
            data = dataset.read(
                out_shape=(int(dataset.height * 100), int(dataset.width * 100)),
                # Reduce 100 to 10 if using the whole globe
                resampling=Resampling.nearest
            )

        # Convert new resampled array from 3D to 2D
        data = numpy.squeeze(data, axis=0)

        # Specify the filepath of the resampled raster
        resample_filename = 'gfs_apcp_' + today_str + '_hrs' + file[-11:-4] + '_resampled.tif'
        resample_filepath = os.path.join(resample_folder, resample_filename)

        # Save the GeoTIFF
        with rasterio.open(
                resample_filepath,
                'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                nodata=numpy.nan,
                crs='+proj=latlong',
                transform=geotransform_res,
        ) as dst:
            dst.write(data, 1)

    return resample_folder


def zonal_statistics(region, resample_folder):
    """
    Script to calculate average precip over FFGS polygon shapefile
    :param resample_folder:
    :return: csv file with the zonal statistics
    """
    # Define app workspace and sub-paths
    app_ws = app_configuration()['app_wksp_path']
    shp_path = os.path.join(app_ws, 'shapefiles/ffgs_hisp_GCS_WGS_1984.shp')
    today = datetime.datetime.utcnow()
    today_str = today.strftime("%Y%m%d")
    stat_file = os.path.join(app_ws, 'zonal_stats_' + today_str + '_00.csv')


    # List all 10 Resampled GeoTIFFs
    res_tif_list = []
    for i in os.listdir(resample_folder):
        if i[-3:] == 'tif':
            res_tif_list.append(os.path.join(resample_folder, i))
    res_tif_list.sort()


    stats_df = pd.DataFrame()

    # for i in range(3):
    for i in range(len(res_tif_list)):
        ras_path = res_tif_list[i]
        stats = rasterstats.zonal_stats(
            shp_path,
            ras_path,
            stats=['mean'],
            geojson_out=True
            )

        forecast_date = today.strftime("%m/%d/%Y")
        timestep = today + datetime.timedelta(days=(i))
        timestep_str = datetime.datetime.strftime(timestep, "%m/%d/%Y")


        # for j in range(3):
        for j in range(len(stats)):

            temp_data = stats[j]['properties']
            temp_data.update({'Forecast Date':forecast_date})
            temp_data.update({'Timestep':timestep_str})

            temp_df = pd.DataFrame([temp_data])
            stats_df = stats_df.append(temp_df, ignore_index=True)

    print(stats_df)
    stats_df.to_csv(stat_file)

    return stat_file


