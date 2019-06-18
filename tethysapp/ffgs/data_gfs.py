import datetime
import logging
import os
import shutil

import netCDF4
import numpy
import rasterio
import requests
import xarray


def download_gfs(threddspath, timestamp, region):
    logging.info('\nStarting GFS Grib Downloads for ' + region)
    # set filepaths
    gribsdir = os.path.join(threddspath, region, 'gfs', timestamp, 'gribs')

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        logging.info('There is no download folder, you must have already processed them. Skipping download stage.')
        return
    elif len(os.listdir(gribsdir)) >= 40:
        logging.info('There are already 40 forecast steps in here. Dont need to download them')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # # get the parts of the timestamp to put into the url
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%H")
    fc_date = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%Y%m%d")

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084',
                '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168']

    # this is where the actual downloads happen. set the url, filepath, then download
    subregions = {
        'hispaniola': 'subregion=&leftlon=-75&rightlon=-68&toplat=20.5&bottomlat=17',
        'centralamerica': 'subregion=&leftlon=-94.25&rightlon=-75.5&toplat=19.5&bottomlat=5.5',
    }
    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + time + 'z.pgrb2.0p25.f' + step + \
              '&all_lev=on&var_APCP=on&' + subregions[region] + '&dir=%2Fgfs.' + fc_date + '%2F' + time

        fc_timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        file_timestep = fc_timestamp + datetime.timedelta(hours=int(step))
        filename_timestep = datetime.datetime.strftime(file_timestep, "%Y%m%d%H")

        filename = filename_timestep + '.grb'
        logging.info('downloading the file ' + filename)
        filepath = os.path.join(gribsdir, filename)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)

    logging.info('Finished Downloads')
    return


def gfs_tiffs(threddspath, wrksppath, timestamp, region):
    """
    Script to combine 6-hr accumulation grib files into 24-hr accumulation geotiffs.
    Dependencies: datetime, os, numpy, rasterio
    """
    logging.info('\nStarting to process the GFS gribs into GeoTIFFs')
    # declare the environment
    tiffs = os.path.join(wrksppath, region, 'GeoTIFFs')
    gribs = os.path.join(threddspath, region, 'gfs', timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, region, 'gfs', timestamp, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    if not os.path.exists(gribs):
        logging.info('There is no gribs folder, you must have already run this step. Skipping conversions')
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
    files.sort()

    # Read raster dimensions only once to apply to all rasters
    path = os.path.join(gribs, files[0])
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
    for i in files:
        logging.info('working on file ' + i)
        path = os.path.join(gribs, i)
        src = rasterio.open(path)
        file_array = src.read(1)

        # using the last grib file for the day (path) convert it to a netcdf and set the variable to file_array
        logging.info('opening grib file ' + path)
        obj = xarray.open_dataset(path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        logging.info('converting it to a netcdf')
        ncname = i.replace('.grb', '.nc')
        logging.info('saving it to the path ' + path)
        ncpath = os.path.join(netcdfs, ncname)
        obj.to_netcdf(ncpath, mode='w')
        logging.info('converted')
        logging.info('writing the correct values to the tp array')
        nc = netCDF4.Dataset(ncpath, 'a')
        nc['tp'][:] = file_array
        nc.close()
        logging.info('created a netcdf')

        # Specify the GeoTIFF filepath
        tif_filename = i.replace('grb', 'tif')
        tif_filepath = os.path.join(tiffs, tif_filename)

        # Save the 24-hr raster
        with rasterio.open(
                tif_filepath,
                'w',
                driver='GTiff',
                height=file_array.shape[0],
                width=file_array.shape[1],
                count=1,
                dtype=file_array.dtype,
                nodata=numpy.nan,
                crs='+proj=latlong',
                transform=geotransform,
        ) as dst:
            dst.write(file_array, 1)
        logging.info('wrote it to a GeoTIFF\n')

    # # clear the gribs folder now that we're done with this
    shutil.rmtree(gribs)

    return
