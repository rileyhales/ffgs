import logging
import math
import shutil

import netCDF4
import numpy
import pandas as pd
import rasterio
import rasterstats
from rasterio.enums import Resampling

from .options import *

# todo only do 6-hr timesteps
# todo add max to rasterstats calculation

def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_settings (options)
    """
    logging.info('\nSetting the Environment')
    # determine the most day and hour of the day timestamp of the most recent GFS forecast
    now = datetime.datetime.utcnow()
    if now.hour > 21:
        timestamp = now.strftime("%Y%m%d") + '18'
    elif now.hour > 15:
        timestamp = now.strftime("%Y%m%d") + '12'
    elif now.hour > 9:
        timestamp = now.strftime("%Y%m%d") + '06'
    elif now.hour > 3:
        timestamp = now.strftime("%Y%m%d") + '00'
    else:
        now = now - datetime.timedelta(days=1)
        timestamp = now.strftime("%Y%m%d") + '18'
    logging.info('determined the timestamp to download: ' + timestamp)

    # set folder paths for the environment
    configuration = app_settings()
    threddspath = configuration['threddsdatadir']
    wrksppath = configuration['app_wksp_path']

    # perform a redundancy check, if the last timestamp is the same as current, abort the workflow
    timefile = os.path.join(wrksppath, 'timestamp.txt')
    with open(timefile, 'r') as file:
        lasttime = file.readline()
        if lasttime == timestamp:
            redundant = True
            logging.info('The last recorded timestamp is the timestamp we determined, aborting workflow')
            return threddspath, wrksppath, timestamp, redundant
        else:
            redundant = False

    # if the file structure already exists, quit
    checkthredds = os.path.join(threddspath, 'hispaniola', 'gfs', timestamp)
    checkworkspace = os.path.join(wrksppath, 'hispaniola', 'GeoTIFFs_resampled')
    if os.path.exists(checkthredds) and os.path.exists(checkworkspace):
        logging.info('You have a file structure for this timestep but didnt complete the workflow, analyzing...')
        return threddspath, wrksppath, timestamp, redundant

    # create the file structure for the new data
    for region in ffgs_regions():
        logging.info('Creating new App Workspace GeoTIFF file structure for ' + region[1])
        new_dir = os.path.join(wrksppath, region[1], 'GeoTIFFS')
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        os.chmod(new_dir, 0o777)
        new_dir = os.path.join(wrksppath, region[1], 'GeoTIFFs_resampled')
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        os.chmod(new_dir, 0o777)
        logging.info('Creating new THREDDS file structure for ' + region[1])
        for model in ('gfs',):
            new_dir = os.path.join(threddspath, region[1], model)
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
            os.mkdir(new_dir)
            os.chmod(new_dir, 0o777)
            new_dir = os.path.join(threddspath, region[1], model, timestamp)
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
            os.mkdir(new_dir)
            os.chmod(new_dir, 0o777)
            for filetype in ('gribs', 'netcdfs', 'processed'):
                new_dir = os.path.join(threddspath, region[1], model, timestamp, filetype)
                if os.path.exists(new_dir):
                    shutil.rmtree(new_dir)
                os.mkdir(new_dir)
                os.chmod(new_dir, 0o777)

    logging.info('All done, on to do work')
    return threddspath, wrksppath, timestamp, redundant


def resample(wrksppath, timestamp, region):
    """
    Script to resample rasters from .25 o .0025 degree in order for rasterstats to work
    Dependencies: datetime, os, numpy, rasterio
    """
    logging.info('\nResampling the rasters for ' + region)
    # Define app workspace and sub-paths
    tiffs = os.path.join(wrksppath, region, 'GeoTIFFS')
    resampleds = os.path.join(wrksppath, region, 'GeoTIFFs_resampled')

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
    geotransform_res = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width * 100, height * 100)

    # Resample each GeoTIFF
    for file in files:
        path = os.path.join(tiffs, file)
        logging.info(path)
        with rasterio.open(path) as dataset:
            data = dataset.read(
                out_shape=(int(dataset.height * 100), int(dataset.width * 100)),
                # Reduce 100 to 10 if using the whole globe
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


def zonal_statistics(wrksppath, timestamp, region, model):
    """
    Script to calculate average precip over FFGS polygon shapefile
    Dependencies: datetime, os, pandas, rasterstats
    """
    logging.info('\nDoing Zonal Statistics on ' + region)
    # Define app workspace and sub-paths
    resampleds = os.path.join(wrksppath, region, 'GeoTIFFs_resampled')
    shp_path = os.path.join(wrksppath, region, 'shapefiles', 'ffgs_' + region + '.shp')

    stat_file = os.path.join(wrksppath, region, model + 'results.csv')

    # check that there are resampled tiffs to do zonal statistics on
    if not os.path.exists(resampleds):
        logging.info('There are no resampled tiffs to do zonal statistics on. Skipping Zonal Statistics')
        return

    # List all Resampled GeoTIFFs
    files = os.listdir(resampleds)
    files = [tif for tif in files if tif.endswith('.tif')]
    files.sort()

    stats_df = pd.DataFrame()

    # do the zonal statistics for each resampled tiff file
    for i in range(len(files)):
        logging.info('\nstarting zonal statistics for file ' + files[i])
        ras_path = os.path.join(resampleds, files[i])
        stats = rasterstats.zonal_stats(
            shp_path,
            ras_path,
            stats=['count','mean', 'max'],
            geojson_out=True
            )

        timestep = files[i][:10]

        # for each stat that you get out, write it to the dataframe
        logging.info('writing the statistics for this file to the dataframe')
        for j in range(len(stats)):

            temp_data = stats[j]['properties']
            temp_data.update({'Timestamp': timestamp})
            temp_data.update({'Timestep': timestep})

            temp_df = pd.DataFrame([temp_data])
            stats_df = stats_df.append(temp_df, ignore_index=True)
        logging.info('done')

    # write the resulting dataframe to a csv
    logging.info('\ndone with zonal statistics, writing to a csv file')
    stats_df.to_csv(stat_file)

    # delete the resampled tiffs now that we dont need them
    logging.info('deleting the resampled tiffs directory')
    shutil.rmtree(resampleds)

    return


def nc_georeference(threddspath, timestamp, region, model):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime
    see github/rileyhales/datatools for more details
    """
    logging.info('\nProcessing the netCDF files')

    # setting the environment file paths
    netcdfs = os.path.join(threddspath, region, model, timestamp, 'netcdfs')
    processed = os.path.join(threddspath, region, model, timestamp, 'processed')

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
    lat_min = -90
    lon_min = -180
    lat_step = .25
    lon_step = .25
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
        lat_list = [lat_min + i * lat_step for i in range(dimensions['lat'])]
        lon_list = [lon_min + i * lon_step for i in range(dimensions['lon'])]
        duplicate['lat'][:] = lat_list
        duplicate['lon'][:] = lon_list

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


def new_ncml(threddspath, timestamp, region, model):
    logging.info('\nWriting a new ncml file for this date')
    # create a new ncml file by filling in the template with the right dates and writing to a file
    ncml = os.path.join(threddspath, region, model, 'wms.ncml')
    date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
    with open(ncml, 'w') as file:
        file.write(
            '<netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">\n'
            '    <variable name="time" type="int" shape="time">\n'
            '        <attribute name="units" value="days since ' + date + '"/>\n'
            '        <attribute name="_CoordinateAxisType" value="Time" />\n'
            '        <values start="0" increment="1" />\n'
            '    </variable>\n'
            '    <aggregation dimName="time" type="joinExisting" recheckEvery="1 hour">\n'
            '        <scan location="' + timestamp + '/processed/"/>\n'
            '    </aggregation>\n'
            '</netcdf>'
        )
    logging.info('Wrote New .ncml')
    return


def new_colorscales(wrksppath, region, model):
    # set the environment
    logging.info('\nGenerating a new color scale csv for the ' + model + ' results')
    colorscales = os.path.join(wrksppath, region, model + 'colorscales.csv')
    results = os.path.join(wrksppath, region, model + 'results.csv')
    answers = pd.DataFrame(columns=['cat_id', 'mean', 'max'])

    # read the dataframe and extract the values
    res_df = pd.read_csv(results)[['cat_id', 'mean', 'max']]
    ids = res_df.cat_id.unique()
    for catid in ids:
        df = res_df.query("cat_id == @catid")
        mean = max(df['mean'].values)
        maximum = max(df['max'].values)
        answers.append({'cat_id': catid, 'mean': mean, 'max': maximum})

    answers.to_csv(colorscales)

    return


def set_wmsbounds(threddspath, timestamp, region, model):
    """
    Dynamically defines exact boundaries for the legend and wms so that they are synchronized
    Dependencies: netcdf4, os, math, numpy
    """
    logging.info('\nSetting the WMS bounds')
    # get a list of files to
    ncfolder = os.path.join(threddspath, region, model, timestamp, 'processed')
    ncs = os.listdir(ncfolder)
    files = [file for file in ncs if file.startswith('processed')][0]

    # setup the dictionary of values to return
    bounds = {}
    variables = {}  # gfs_variables()
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


def cleanup(threddspath, wrksppath, timestamp, region, model):
    # write a file with the current timestep triggering the app to start using this data
    logging.info('\nPerforming file cleanup')
    logging.info('writing the timestamp used for this run to a textfile')
    with open(os.path.join(wrksppath, 'timestamp.txt'), 'w') as file:
        file.write(timestamp)

    # delete anything that isn't the new folder of data (named for the timestamp) or the new wms.ncml file
    logging.info('Getting rid of old ' + model + ' data folders')
    path = os.path.join(threddspath, region, model)
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
