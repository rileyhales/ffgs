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

# todo always append to existing csv, rename the csv without the date
# todo add resample and zonal_statsistics to ajax.py (or controllers)
# todo delete old tiffs, add checks to the start of the function to see if we need to skip


def gfs_24hrfiles(threddspath, wrksppath, timestamp, region):
    """
    Script to combine 6-hr accumulation grib files into 24-hr accumulation geotiffs.
    Dependencies: datetime, os, numpy, rasterio
    :param gfs_folder: folder where grib files were downloaded
    :return: folder with daily precipitaion geotiffs
    """
    print('\nStarting to process the GFS gribs into 24 hour files')
    # declare the environment
    tiffs = os.path.join(wrksppath, region, '24_hr_GeoTIFFs')
    gribs = os.path.join(threddspath, region, 'gfs', timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, region, 'gfs', timestamp, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    if not os.path.exists(gribs):
        print('There are no gribs to convert, you must have already run this step. Skipping conversions')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial conversion)
    else:
        shutil.rmtree(netcdfs)
        os.mkdir(netcdfs)
        os.chmod(netcdfs, 0o777)
        shutil.rmtree(tiffs)
        os.mkdir(tiffs)
        os.chmod(tiffs, 0o777)

    # create a list of all the files of type grib and convert to a list of their file paths
    files = os.listdir(gribs)
    files = [grib for grib in files if grib.endswith('.grb')]
    files = [os.path.join(gribs, grib) for grib in files]
    files.sort()

    # Split list into a list of lists containing the 4 daily files
    n = 4
    daily_file_list = [files[j*n:(j+1)*n] for j in range((len(files) + n -1)//n)]

    # Read raster dimensions only once to apply to all rasters
    path = os.path.join(daily_file_list[0][0])
    raster_dim = rasterio.open(path)
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

        # Copy raster to 2D Array and add each 6-hour accumulation into a daily accumulation array
        for j in range(len(i)):
            print('working on file ' + i[j])
            file = i[j]
            src = rasterio.open(file)
            six_hr_array = src.read(1)
            daily_array = daily_array + six_hr_array
        print('calculated a daily array')

        # todo this is where the app should make a netcdf of the daily_array values
        # makenetcdf(threddspath, wrksppath, timestamp, region, dailyarray)

        # Specify the filepath for the 24-hr raster
        last_hr = int(i[-1][-7:-4])
        start_hr = str(last_hr-24).rjust(3,'0')
        end_hr = str(last_hr).rjust(3,'0')
        daily_filename = 'gfs_apcp_' + timestamp + '_hrs' + start_hr + '-' + end_hr + '.tif'
        daily_filepath = os.path.join(tiffs, daily_filename)
        print('save path is ' + daily_filepath)

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
        print('wrote it to a GeoTIFF')

    return daily_array


def resample(wrksppath, timestamp, region):
    """
    Script to resample rasters from .25 o .0025 degree in order for rasterstats to work
    Dependencies: datetime, os, numpy, rasterio
    :param gfs_folder: folder of raw grib data and other new directories
    :param daily_folder: folder of 24-hr GeoTIFFs
    :return: resample_folder: folder of 24-hr resampled GeoTIFFs
    """
    print('\nResampleing the rasters for ' + region)
    # Define app workspace and sub-paths
    tiffs = os.path.join(wrksppath, region, '24_hr_GeoTIFFs')
    resampleds = os.path.join(wrksppath, region, '24_hr_GeoTIFFs_resampled')
    shp_path = os.path.join(wrksppath, region, 'shapefiles', 'ffgs_' + region + '.shp')
    stat_file = os.path.join(wrksppath, 'zonal_stats_' + timestamp + '_00.csv')

    # List all 10 Resampled GeoTIFFs
    files = os.listdir(tiffs)
    files = [tif for tif in files if tif.endswith('.tif')]
    files.sort()

    # Create directory for the resampled GeoTIFFs
    if os.path.exists(resampleds):
        print('Path already exists and will be deleted.')
        shutil.rmtree(resampleds)
        os.mkdir(resampleds)
    else:
        os.mkdir(resampleds)

    # Read raster dimensions
    path = os.path.join(tiffs, files[0])
    raster_dim = rasterio.open(path)
    width = raster_dim.width
    height = raster_dim.height
    lon_min = raster_dim.bounds.left
    lon_max = raster_dim.bounds.right
    lat_min = raster_dim.bounds.bottom
    lat_max = raster_dim.bounds.top

    # Geotransform for each 24-hr resampled raster (east, south, west, north, width, height)
    geotransform_res = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width * 100, height * 100)

    # Resample each GeoTIFF
    for file in files:
        path = os.path.join(tiffs, file)
        print(path)
        with rasterio.open(path) as dataset:
            data = dataset.read(
                out_shape=(int(dataset.height * 100), int(dataset.width * 100)),
                # Reduce 100 to 10 if using the whole globe
                resampling=Resampling.nearest
            )

        # Convert new resampled array from 3D to 2D
        data = numpy.squeeze(data, axis=0)

        # Specify the filepath of the resampled raster
        resample_filename = 'gfs_apcp_' + timestamp + '_hrs' + file[-11:-4] + '_resampled.tif'
        resample_filepath = os.path.join(resampleds, resample_filename)

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

    return


def zonal_statistics(wrksppath, timestamp, region):
    """
    Script to calculate average precip over FFGS polygon shapefile
    Dependencies: datetime, os, pandas, rasterstats
    :param region: which shapefile to use
    :param resample_folder: folder with resampled GeoTIFFs
    :return: csv file with the zonal statistics
    """
    print('\nDoing Zonal Statistics on ' + region)
    # Define app workspace and sub-paths
    resampleds = os.path.join(wrksppath, region, '24_hr_GeoTIFFs_resampled')
    shp_path = os.path.join(wrksppath, region, 'shapefiles', 'ffgs_' + region + '.shp')
    stat_file = os.path.join(wrksppath, 'zonal_stats_' + timestamp + '_00.csv')

    # List all 10 Resampled GeoTIFFs
    files = os.listdir(resampleds)
    files = [tif for tif in files if tif.endswith('.tif')]
    files.sort()

    stats_df = pd.DataFrame()

    # for i in range(3):
    for i in range(len(files)):
        ras_path = os.path.join(resampleds, files[i])
        stats = rasterstats.zonal_stats(
            shp_path,
            ras_path,
            stats=['mean'],
            geojson_out=True
            )

        today = datetime.datetime.utcnow()
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


