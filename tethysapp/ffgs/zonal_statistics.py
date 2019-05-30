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

# todo add region to resample function
# todo combine 24hr tiff and netcdf
# todo put tiffs in workspace
# todo always append to existing csv, rename the csv without the date
# todo add resample and zonal_statsistics to ajax.py (or controllers)

def make_gfs_24hrTiffs(gfs_folder):
    """
    Script to combine 6-hr accumulation grib files into 24-hr accumulation geotiffs.
    Dependencies: datetime, os, numpy, rasterio
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
    Dependencies: datetime, os, numpy, rasterio
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
    Dependencies: datetime, os, pandas, rasterstats
    :param region: which shapefile to use
    :param resample_folder: folder with resampled GeoTIFFs
    :return: csv file with the zonal statistics
    """
    # Define app workspace and sub-paths
    app_ws = app_configuration()['app_wksp_path']
    shp_path = os.path.join(app_ws, 'shapefiles', region, 'ffgs_hisp_GCS_WGS_1984.shp')
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
            temp_data.update({'Forecast Date': forecast_date})
            temp_data.update({'Timestep': timestep_str})

            temp_df = pd.DataFrame([temp_data])
            stats_df = stats_df.append(temp_df, ignore_index=True)

    print(stats_df)
    stats_df.to_csv(stat_file)

    return stat_file


