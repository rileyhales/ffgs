import logging
import math
import shutil

import netCDF4
import numpy
import pandas as pd
import rasterio
import rasterstats
import requests
import xarray
from rasterio.enums import Resampling

from .options import *


def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_settings (options)
    """
    logging.info('\nSetting the Environment')
    # determine the most day and hour of the day timestamp of the most recent WRF-PR forecast
    now = datetime.datetime.utcnow()
    if now.hour > 20:
        timestamp = now.strftime("%Y%m%d") + '18'
    elif now.hour > 8:
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
        else:
            redundant = False

    # if the file structure already exists, quit
    chk_hisp = os.path.join(wrksppath, 'hispaniola', 'wrfpr_GeoTIFFs_resampled')

    if os.path.exists(chk_hisp):
        logging.info('You have a file structure for this timestep but didnt complete the workflow, analyzing...')
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
        url = 'https://www.ftp.ncep.noaa.gov/data/nccf/com/hiresw/prod/hiresw.' + \
              fc_date + '/hiresw.t' + time + 'z.arw_5km.f' + step + '.pr.grib2'

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
            file_array = src.read(284)
        else:
            cum_file = os.path.join(gribs, i)
            cum_src = rasterio.open(cum_file)
            cum_array = cum_src.read(284)

            past_file = os.path.join(gribs, files[j-1])
            past_src = rasterio.open(past_file)
            past_array = past_src.read(284)

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


def zonal_statistics(wrksppath, timestamp, region):
    """
    Script to calculate average precip over FFGS polygon shapefile
    Dependencies: datetime, os, pandas, rasterstats
    """
    logging.info('\nDoing Zonal Statistics on ' + region)
    # Define app workspace and sub-paths
    resampleds = os.path.join(wrksppath, region, 'wrfpr_GeoTIFFs_resampled')
    shp_path = os.path.join(wrksppath, region, 'shapefiles', 'ffgs_' + region + '.shp')

    stat_file = os.path.join(wrksppath, region, 'wrfprresults.csv')

    # check that there are resampled tiffs to do zonal statistics on
    if not os.path.exists(resampleds):
        logging.info('There are no resampled tiffs to do zonal statistics on. Skipping Zonal Statistics')
        return

    # List all Resampled GeoTIFFs
    files = os.listdir(resampleds)
    files = [tif for tif in files if tif.endswith('.tif')]
    files.sort()

    # do zonal statistics for each resampled tiff file and put it in the stats dataframe
    stats_df = pd.DataFrame()
    for i in range(len(files)):
        logging.info('starting zonal statistics for ' + files[i])
        ras_path = os.path.join(resampleds, files[i])
        stats = rasterstats.zonal_stats(
            shp_path,
            ras_path,
            stats=['count', 'max', 'mean'],
            geojson_out=True
            )

        timestep = files[i][:10]

        # for each stat that you get out, write it to the dataframe
        logging.info('writing the statistics for this file to the dataframe')
        for j in range(len(stats)):

            temp_data = stats[j]['properties']
            temp_data.update({'Forecast Timestamp': timestamp})
            temp_data.update({'Timestep': timestep})

            temp_df = pd.DataFrame([temp_data])
            stats_df = stats_df.append(temp_df, ignore_index=True)

    # write the resulting dataframe to a csv
    logging.info('\ndone with zonal statistics, rounding values, writing to a csv file')
    stats_df = stats_df.round({'max': 1, 'mean': 1})
    stats_df.to_csv(stat_file, index=False)

    # delete the resampled tiffs now that we dont need them
    logging.info('deleting the resampled tiffs directory')
    shutil.rmtree(resampleds)

    return


def nc_georeference(threddspath, timestamp, region):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime
    see github/rileyhales/datatools for more details
    """
    logging.info('\nProcessing the netCDF files')

    # setting the environment file paths
    netcdfs = os.path.join(threddspath, region, 'wrfpr', timestamp, 'netcdfs')
    processed = os.path.join(threddspath, region, 'wrfpr', timestamp, 'processed')

    # if you already have processed netcdfs files, skip this and quit the function
    if not os.path.exists(netcdfs):
        logging.info('There are no netcdfs to be converted. Skipping netcdf processing.')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial processing)
    else:
        shutil.rmtree(processed)
        os.mkdir(processed)
        os.chmod(processed, 0o777)

    # list the files that need to be converted
    net_files = os.listdir(netcdfs)
    files = [file for file in net_files if file.endswith('.nc')]
    logging.info('There are ' + str(len(files)) + ' compatible files.')

    # read the first file that we'll copy data from in the next blocks of code
    logging.info('Preparing the reference file')
    path = os.path.join(netcdfs, net_files[0])
    netcdf_obj = netCDF4.Dataset(path, 'r', clobber=False, diskless=True)

    # get a dictionary of the dimensions and their size and rename the north/south and east/west ones
    dimensions = {}
    for dimension in netcdf_obj.dimensions.keys():
        dimensions[dimension] = netcdf_obj.dimensions[dimension].size
    dimensions['lat'] = dimensions['latitude']
    dimensions['lon'] = dimensions['longitude']
    dimensions['time'] = 1
    del dimensions['latitude'], dimensions['longitude']

    # get a list of the variables and remove the one's i'm going to 'manually' correct
    variables = netcdf_obj.variables
    del variables['valid_time'], variables['step'], variables['latitude'], variables['longitude'], variables['surface']
    variables = variables.keys()

    # min lat and lon and the interval between values (these are static values
    netcdf_obj.close()

    # this is where the files start getting copied
    for file in files:
        logging.info('Working on file ' + str(file))
        openpath = os.path.join(netcdfs, file)
        savepath = os.path.join(processed, 'processed_' + file)
        # open the file to be copied
        original = netCDF4.Dataset(openpath, 'r', clobber=False, diskless=True)
        duplicate = netCDF4.Dataset(savepath, 'w', clobber=True, format='NETCDF4', diskless=False)
        # set the global netcdf attributes - important for georeferencing
        duplicate.setncatts(original.__dict__)

        # specify dimensions from what we copied before
        for dimension in dimensions:
            duplicate.createDimension(dimension, dimensions[dimension])

        # 'Manually' create the dimensions that need to be set carefully
        duplicate.createVariable(varname='lat', datatype='f4', dimensions='lat')
        duplicate.createVariable(varname='lon', datatype='f4', dimensions='lon')

        # create the lat and lon values as a 1D array
        duplicate['lat'][:] = original['latitude'][:]
        duplicate['lon'][:] = original['longitude'][:]

        # set the attributes for lat and lon (except fill value, you just can't copy it)
        for attr in original['latitude'].__dict__:
            if attr != "_FillValue":
                duplicate['lat'].setncattr(attr, original['latitude'].__dict__[attr])
        for attr in original['longitude'].__dict__:
            if attr != "_FillValue":
                duplicate['lon'].setncattr(attr, original['longitude'].__dict__[attr])

        # copy the rest of the variables
        hour = 6
        for variable in variables:
            # check to use the lat/lon dimension names
            dimension = original[variable].dimensions
            if 'latitude' in dimension:
                dimension = list(dimension)
                dimension.remove('latitude')
                dimension.append('lat')
                dimension = tuple(dimension)
            if 'longitude' in dimension:
                dimension = list(dimension)
                dimension.remove('longitude')
                dimension.append('lon')
                dimension = tuple(dimension)
            if len(dimension) == 2:
                dimension = ('time', 'lat', 'lon')
            if variable == 'time':
                dimension = ('time',)

            # create the variable
            duplicate.createVariable(varname=variable, datatype='f4', dimensions=dimension)

            # copy the arrays of data and set the timestamp/properties
            date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
            date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
            if variable == 'time':
                duplicate[variable][:] = [hour]
                hour = hour + 6
                duplicate[variable].long_name = original[variable].long_name
                duplicate[variable].units = "hours since " + date
                duplicate[variable].axis = "T"
                # also set the begin date of this data
                duplicate[variable].begin_date = timestamp
            if variable == 'lat':
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "Y"
            if variable == 'lon':
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "X"
            else:
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "lat lon"
            duplicate[variable].long_name = original[variable].long_name
            duplicate[variable].begin_date = timestamp
            duplicate[variable].units = original[variable].units

        # close the files, delete the one you just did, start again
        original.close()
        duplicate.sync()
        duplicate.close()

    # delete the netcdfs now that we're done with them triggering future runs to skip this step
    shutil.rmtree(netcdfs)

    logging.info('Finished File Conversions')
    return


def new_ncml(threddspath, timestamp, region):
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
            '        <values start="6" increment="6" />\n'
            '    </variable>\n'
            '    <aggregation dimName="time" type="joinExisting" recheckEvery="1 hour">\n'
            '        <scan location="' + timestamp + '/processed/"/>\n'
            '    </aggregation>\n'
            '</netcdf>'
        )
    logging.info('Wrote New .ncml')
    return


def new_colorscales(wrksppath, region):
    # set the environment
    logging.info('\nGenerating a new color scale csv for the WRF-PR results')
    colorscales = os.path.join(wrksppath, region, 'wrfprcolorscales.csv')
    results = os.path.join(wrksppath, region, 'wrfprresults.csv')
    logging.info(results)
    answers = pd.DataFrame(columns=['cat_id', 'cum_mean', 'mean', 'max'])

    res_df = pd.read_csv(results, index_col=False)[['cat_id', 'mean', 'max']]
    ids = res_df.cat_id.unique()
    for catid in ids:
        df = res_df.query("cat_id == @catid")
        cum_mean = round(sum(df['mean'].values), 1)
        mean = max(df['mean'].values)
        maximum = max(df['max'].values)
        answers = answers.append({'cat_id': catid, 'cum_mean': cum_mean, 'mean': mean, 'max': maximum}, ignore_index=True)

    answers.to_csv(colorscales, mode='w', index=False)
    logging.info('Wrote new rules to csv')
    return


def set_wmsbounds(threddspath, timestamp, region):
    """
    Dynamically defines exact boundaries for the legend and wms so that they are synchronized
    Dependencies: netcdf4, os, math, numpy
    """
    logging.info('\nSetting the WMS bounds')
    # get a list of files to
    ncfolder = os.path.join(threddspath, region, 'wrfpr', timestamp, 'processed')
    ncs = os.listdir(ncfolder)
    files = [file for file in ncs if file.startswith('processed')][0]

    # setup the dictionary of values to return
    bounds = {}
    variables = {}  # wrfpr_variables()
    for variable in variables:
        bounds[variables[variable]] = ''

    path = os.path.join(ncfolder, files)
    dataset = netCDF4.Dataset(path, 'r')
    logging.info('working on file ' + path)

    for variable in variables:
        logging.info('checking for variable ' + variable)
        array = dataset[variables[variable]][:]
        array = array.flatten()
        array = array[~numpy.isnan(array)]
        maximum = math.ceil(max(array))
        if maximum == numpy.nan:
            maximum = 0
        logging.info('max is ' + str(maximum))

        minimum = math.floor(min(array))
        if minimum == numpy.nan:
            minimum = 0
        logging.info('min is ' + str(minimum))

        bounds[variables[variable]] = str(minimum) + ',' + str(maximum)
    dataset.close()

    logging.info('done checking for max/min. writing the file')
    boundsfile = os.path.join(os.path.dirname(__file__), 'public', 'js', 'bounds.js')
    with open(boundsfile, 'w') as file:
        file.write('const bounds = ' + str(bounds) + ';')
    logging.info('wrote the js file')
    return


def cleanup(threddspath, timestamp, region):
    # delete anything that isn't the new folder of data (named for the timestamp) or the new wms.ncml file
    logging.info('Getting rid of old WRF-PR data folders')
    path = os.path.join(threddspath, region, 'wrfpr')
    files = os.listdir(path)
    files.remove(timestamp)
    files.remove('wms.ncml')
    for file in files:
        try:
            shutil.rmtree(os.path.join(path, file))
        except:
            os.remove(os.path.join(path, file))

    logging.info('Done')
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

    # run the workflow for each region, for each model in that region
    region = 'hispaniola'
    logging.info('\nBeginning to process ' + region + ' on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    # download each forecast model, convert them to netcdfs and tiffs
    succeeded = download_wrfpr(threddspath, timestamp, region)
    if not succeeded:
        return 'Workflow Aborted- Downloading Errors Occurred'
    wrfpr_tiffs(threddspath, wrksppath, timestamp, region)
    resample(wrksppath, region)
    # the geoprocessing functions
    zonal_statistics(wrksppath, timestamp, region)
    nc_georeference(threddspath, timestamp, region)
    # generate color scales and ncml aggregation files
    new_ncml(threddspath, timestamp, region)
    new_colorscales(wrksppath, region)
    set_wmsbounds(threddspath, timestamp, region)
    # cleanup the workspace by removing old files
    cleanup(threddspath, timestamp, region)

    logging.info('\nAll regions and models finished- writing the timestamp used on this run to a txt file')
    with open(os.path.join(wrksppath, 'wrfpr_timestamp.txt'), 'w') as file:
        file.write(timestamp)

    logging.info('WRF-PR Workflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    logging.info('If there are other model workflows to be processed, they will follow.\n\n\n')

    return 'WRF-PR Workflow Completed- Normal Finish'
