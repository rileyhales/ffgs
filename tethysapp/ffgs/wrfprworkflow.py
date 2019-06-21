import logging
import shutil

import netCDF4
import numpy
import rasterio
import requests
import xarray
from rasterio.enums import Resampling

from .gfsworkflow import nc_georeference, zonal_statistics, new_colorscales, cleanup
from .options import *


def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_settings (options)
    """
    logging.info('\nSetting the Environment for a WRFPR model run')
    # determine the most day and hour of the day timestamp of the most recent WRF-PR forecast
    now = datetime.datetime.utcnow()
    if now.hour > 21:
        timestamp = now.strftime("%Y%m%d") + '18'
    elif now.hour > 9:
        timestamp = now.strftime("%Y%m%d") + '06'
    else:
        now = now - datetime.timedelta(days=1)
        timestamp = now.strftime("%Y%m%d") + '18'
    logging.info('determined the timestamp to download: ' + timestamp)

    # set folder paths for the environment
    configuration = app_settings()
    threddspath = configuration['threddsdatadir']
    wrksppath = configuration['app_wksp_path']

    # perform a redundancy check, if the last timestamp is the same as current, abort the workflow
    timefile = os.path.join(wrksppath, 'wrfpr_timestamp.txt')
    with open(timefile, 'r') as file:
        lasttime = file.readline()
        if lasttime == timestamp:
            redundant = True
            logging.info('The last recorded timestamp is the timestamp we determined, aborting workflow')
            return threddspath, wrksppath, timestamp, redundant
        elif lasttime == 'clobbered':
            # if you marked clobber is true, dont check for old folders from partially completed workflows
            redundant = False
        else:
            # if the file structure already exists, quit
            redundant = False
            chk_hisp = os.path.join(wrksppath, 'hispaniola', 'wrfpr_GeoTIFFs_resampled')
            if os.path.exists(chk_hisp):
                logging.info('There are directories for this timestep but the workflow wasn\'t finished. Analyzing...')
                return threddspath, wrksppath, timestamp, redundant

    # create the file structure and their permissions for the new data
    region = 'hispaniola'
    logging.info('Creating APP WORKSPACE (GeoTIFF) file structure for ' + region)
    new_dir = os.path.join(wrksppath, region, 'wrfpr_GeoTIFFs')
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    new_dir = os.path.join(wrksppath, region, 'wrfpr_GeoTIFFs_resampled')
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    logging.info('Creating THREDDS file structure for ' + region)
    new_dir = os.path.join(threddspath, region, 'wrfpr')
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    new_dir = os.path.join(threddspath, region, 'wrfpr', timestamp)
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    for filetype in ('gribs', 'netcdfs', 'processed'):
        new_dir = os.path.join(threddspath, region, 'wrfpr', timestamp, filetype)
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        os.chmod(new_dir, 0o777)

    logging.info('All done setting up folders, on to do work')
    return threddspath, wrksppath, timestamp, redundant


def download_wrfpr(threddspath, timestamp, region):
    """
    Script to download WRF-PuertoRico Grib Files.
    Dependencies: datetime, os, requests, shutil
    """
    logging.info('\nStarting WRF-PR Grib Downloads')
    # set filepaths
    gribsdir = os.path.join(threddspath, region, 'wrfpr', timestamp, 'gribs')

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        logging.info('There is no download folder, you must have already processed them. Skipping download stage.')
        return True
    elif len(os.listdir(gribsdir)) >= 48:
        logging.info('There are already 48 forecast steps in here. Dont need to download them')
        return True
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # # get the parts of the timestamp to put into the url
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%H")
    fc_date = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%Y%m%d")

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',
                '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
                '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36',
                '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48']

    # this is where the actual downloads happen. set the url, filepath, then download
    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_hirespr.pl?file=hiresw.t' + time + 'z.arw_5km.f' + step + \
              '.pr.grib2&lev_surface=on&var_APCP=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fhiresw.' + \
              fc_date

        fc_timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        file_timestep = fc_timestamp + datetime.timedelta(hours=int(step))
        filename_timestep = datetime.datetime.strftime(file_timestep, "%Y%m%d%H")

        filename = filename_timestep + '.grb'
        logging.info('downloading the file ' + filename)
        filepath = os.path.join(gribsdir, filename)
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
        except requests.HTTPError as e:
            errorcode = e.response.status_code
            logging.info('\nHTTPError ' + str(errorcode) + ' downloading ' + filename + ' from\n' + url)
            if errorcode == 404:
                logging.info('The file was not found on the server, trying an older forecast time')
            elif errorcode == 500:
                logging.info('Probably a problem with the URL. Check the log and try the link')
            return False
    logging.info('Finished Downloads')
    return True


def wrfpr_tiffs(threddspath, wrksppath, timestamp, region):
    """
    Script to convert grib files with multiple variables to Total Accumulated Precipitation GeoTIFFs.
    Dependencies: datetime, os, shutil, numpy, rasterio
    """
    logging.info('\nStarting to process the WRF-PR gribs into GeoTIFFs')
    # declare the environment
    tiffs = os.path.join(wrksppath, region, 'wrfpr_GeoTIFFs')
    gribs = os.path.join(threddspath, region, 'wrfpr', timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, region, 'wrfpr', timestamp, 'netcdfs')

    # if you already have wrf-pr netcdfs in the netcdfs folder, quit the function
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

    # create a list of all the files of type "grb" and convert to a list of their file paths
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

    # Create 1-hr GeoTIFFs and NetCDFs
    for i, j in zip(files, range(len(files))):
        logging.info('working on file ' + i)
        if j == 0:
            path = os.path.join(gribs, i)
            src = rasterio.open(path)
            file_array = src.read(1)
        else:
            cum_file = os.path.join(gribs, i)
            cum_src = rasterio.open(cum_file)
            cum_array = cum_src.read(1)

            past_file = os.path.join(gribs, files[j-1])
            past_src = rasterio.open(past_file)
            past_array = past_src.read(1)

            file_array = cum_array - past_array

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


def resample(wrksppath, region):
    """
    Script to resample rasters to 20x the original resolution in order for rasterstats to work
    Dependencies: datetime, os, numpy, rasterio
    """
    logging.info('\nResampling the rasters for ' + region)
    # Define app workspace and sub-paths
    tiffs = os.path.join(wrksppath, region, 'wrfpr_GeoTIFFs')
    resampleds = os.path.join(wrksppath, region, 'wrfpr_GeoTIFFs_resampled')

    # Create directory for the resampled GeoTIFFs
    if not os.path.exists(tiffs):
        logging.info('There is no tiffs folder. You must have already resampled them. Skipping resampling')
        return

    # List all Resampled GeoTIFFs
    files = os.listdir(tiffs)
    files = [tif for tif in files if tif.endswith('.tif')]
    files.sort()

    # Read raster dimensions
    path = os.path.join(tiffs, files[0])
    raster_dim = rasterio.open(path)
    width = raster_dim.width
    height = raster_dim.height
    lon_min = raster_dim.bounds.left
    lon_max = raster_dim.bounds.right
    lat_min = raster_dim.bounds.bottom
    lat_max = raster_dim.bounds.top

    # Geotransform for each resampled raster (east, south, west, north, width, height)
    geotransform_res = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width * 20, height * 20)

    # Resample each GeoTIFF
    for file in files:
        path = os.path.join(tiffs, file)
        logging.info(path)
        with rasterio.open(path) as dataset:
            data = dataset.read(
                out_shape=(int(dataset.height * 20), int(dataset.width * 20)),
                resampling=Resampling.nearest
            )

        # Convert new resampled array from 3D to 2D
        data = numpy.squeeze(data, axis=0)

        # Specify the filepath of the resampled raster
        resample_filename = file.replace('.tif', '_resampled.tif')
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

    # delete the non-resampled tiffs now that we dont need them
    shutil.rmtree(tiffs)

    return


def new_ncml_wrfpr(threddspath, timestamp, region):
    logging.info('\nWriting a new ncml file for this date')
    # create a new ncml file by filling in the template with the right dates and writing to a file
    ncml = os.path.join(threddspath, region, 'wrfpr', 'wms.ncml')
    date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
    with open(ncml, 'w') as file:
        file.write(
            '<netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">\n'
            '    <variable name="time" type="int" shape="time">\n'
            '        <attribute name="units" value="hours since ' + date + '"/>\n'
            '        <attribute name="_CoordinateAxisType" value="Time" />\n'
            '        <values start="1" increment="1" />\n'
            '    </variable>\n'
            '    <aggregation dimName="time" type="joinExisting" recheckEvery="1 hour">\n'
            '        <scan location="' + timestamp + '/processed/"/>\n'
            '    </aggregation>\n'
            '</netcdf>'
        )
    logging.info('Wrote New .ncml')
    return


def run_wrfpr_workflow():
    """
    The controller for running the workflow to download and process data
    """
    # enable logging to track the progress of the workflow and for debugging
    # logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    # logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # start the workflow by setting the environment
    threddspath, wrksppath, timestamp, redundant = setenvironment()

    # if this has already been done for the most recent forecast, abort the workflow
    if redundant:
        logging.info('\nWorkflow aborted on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        return 'Workflow Aborted: already run for most recent data'

    # run the workflow
    region = 'hispaniola'
    model = 'wrfpr'
    logging.info('\nBeginning to process ' + region + ' on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # download each forecast model, convert them to netcdfs and tiffs
    succeeded = download_wrfpr(threddspath, timestamp, region)
    if not succeeded:
        return 'Workflow Aborted- Downloading Errors Occurred'
    wrfpr_tiffs(threddspath, wrksppath, timestamp, region)
    resample(wrksppath, region)
    # the geoprocessing functions
    zonal_statistics(wrksppath, timestamp, region, model)
    nc_georeference(threddspath, timestamp, region, model)
    # generate color scales and ncml aggregation files
    new_ncml_wrfpr(threddspath, timestamp, region)
    new_colorscales(wrksppath, region, model)
    # cleanup the workspace by removing old files
    cleanup(threddspath, timestamp, region, model)

    logging.info('\nAll regions and models finished- writing the timestamp used on this run to a txt file')
    with open(os.path.join(wrksppath, 'wrfpr_timestamp.txt'), 'w') as file:
        file.write(timestamp)

    logging.info('WRF-PR Workflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    logging.info('If there are other model workflows to be processed, they will follow.\n\n\n')

    return 'WRF-PR Workflow Completed- Normal Finish'
