import shutil
import os
import datetime
import requests
import netCDF4
import rasterio
import numpy
import xarray


def download_gfs(threddspath, timestamp, region):
    print('\nStarting GFS Grib Downloads')
    # set filepaths
    gribsdir = os.path.join(threddspath, region, 'gfs', timestamp, 'gribs')

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        print('There is no download folder, you must have already processed the downloads. Skipping download stage.')
        return
    elif len(os.listdir(gribsdir)) >= 40:
        print('There are already 40 forecast steps in here. Dont need to download them')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # get the parts of the timestamp to put into the url
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%Y%m%d")

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084',
                '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168',
                '174', '180', '186', '192', '198', '204', '210', '216', '222', '228', '234', '240']

    # this is where the actual downloads happen. set the url, filepath, then download
    subregions = {
        'hispaniola': 'subregion=&leftlon=-75&rightlon=-68&toplat=20&bottomlat=-17'
    }
    for step in fc_steps:
        # url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t00z.pgrb2.0p25.f" + step + \
        #       "&all_lev=on&var_APCP=on&leftlon=-75&rightlon=-68&toplat=20&bottomlat=17&dir=%2Fgfs." + today_str + "00"
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t00z.pgrb2.0p25.f' + step + \
              '&all_lev=on&var_APCP=on&' + subregions[region] + '&dir=%2Fgfs.' + time + '00'
        filename = 'gfs_apcp_' + timestamp + '_' + step + '.grb'
        print('downloading the file ' + filename)
        filepath = os.path.join(gribsdir, filename)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)

    print('Finished Downloads')
    return


def gfs_24hrfiles(threddspath, wrksppath, timestamp, region):
    """
    Script to combine 6-hr accumulation grib files into 24-hr accumulation geotiffs.
    Dependencies: datetime, os, numpy, rasterio
    """
    print('\nStarting to process the GFS gribs into 24 hour files')
    # declare the environment
    tiffs = os.path.join(wrksppath, region, '24_hr_GeoTIFFs')
    gribs = os.path.join(threddspath, region, 'gfs', timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, region, 'gfs', timestamp, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    if not os.path.exists(gribs):
        print('There is no gribs folder, you must have already run this step. Skipping conversions')
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

    # Split list into a list of lists containing the 4 daily files
    n = 4
    daily_file_list = [files[j*n:(j+1)*n] for j in range((len(files) + n -1)//n)]

    # Read raster dimensions only once to apply to all rasters
    path = os.path.join(gribs, daily_file_list[0][0])
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
            path = os.path.join(gribs, i[j])
            src = rasterio.open(path)
            six_hr_array = src.read(1)
            daily_array = daily_array + six_hr_array
            path = os.path.join(gribs, i[j])
        print('\ncalculated a daily array')

        # using the last grib file for the day (path) convert it to a netcdf and set the variable to daily_array
        print('opening grib file ' + path)
        obj = xarray.open_dataset(path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        print('converting it to a netcdf')
        ncname = i[j].replace('.grb', '') + '.nc'
        print('saving it to the path ' + path)
        ncpath = os.path.join(netcdfs, ncname)
        obj.to_netcdf(ncpath, mode='w')
        print('converted')
        print('writing the correct values to the tp array')
        nc = netCDF4.Dataset(ncpath, 'a')
        nc['tp'][:] = daily_array
        nc.close()
        print('created a netcdf')

        # Specify the filepath for the 24-hr Tiff raster
        last_hr = int(i[-1][-7:-4])
        start_hr = str(last_hr-24).rjust(3,'0')
        end_hr = str(last_hr).rjust(3,'0')
        daily_filename = 'gfs_apcp_' + timestamp + '_hrs' + start_hr + '-' + end_hr + '.tif'
        daily_filepath = os.path.join(tiffs, daily_filename)

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
        print('wrote it to a GeoTIFF\n')

    # clear the gribs folder now that we're done with this
    shutil.rmtree(gribs)

    return
