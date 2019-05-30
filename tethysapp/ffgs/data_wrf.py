import os
import datetime
import shutil
import requests


def download_wrf(threddspath, timestamp):
    """
    Script to download WRF, import into QGIS,and process
    © Feb 18, 2019 - Chris Edwards, Jake Lewis, Hunter Williams
    Modified for tethys implementation by Riley Hales and Chris Edwards May 22 2019
    WRF Data Information:
    URL: https://www.nco.ncep.noaa.gov/pmb/products/hiresw/
    Model: AWIPS 3.8km Puerto Rico ARW (NCAR Advanced Research WRF, 2.5km doesn't include the DR) (filename says it's 5km)
    Data Access: GRIB2 via urllib
    This model runs twice a day, at 6:00 and 18:00. We use the 6:00
    We use the 24- and 48-hr accumulated precipitation in kg/m^2
    Filename eg: hiresw.t06z.arw_5km.f24.pr.grib2
    The variable APCP (Total Precipitation) is stored in Raster Band 282
    """
    print('\nStarting WRF Grib Downloads')

    # set filepaths
    gribsdir = os.path.join(threddspath, 'hispaniola', 'wrf', timestamp, 'gribs')

    # modify the timestamp for use in the wrf model
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
    time = time.strftime("%Y%m%d")

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        print('There is no download folder, you must have already processed the downloads. Skipping download stage.')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # this is where the actual downloads happen. set the url, filepath, then download

    for step in ['24', '48']:
        url = 'https://www.ftp.ncep.noaa.gov/data/nccf/com/hiresw/prod/hiresw.' + time + \
              '/hiresw.t06z.arw_5km.f' + step + '.pr.grib2'
        filename = 'wrf_' + time + '_f' + step + '.grib'
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
