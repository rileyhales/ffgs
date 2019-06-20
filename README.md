# Flash Flood Guidance System Risk Analyzer
This is a Tethys 2/3 compatible app that helps determine risk of flooding based on the Flash Flood Guidance System using the GFS and WRF forecasts as inputs for precipitation depths.

© [Riley Hales](http://rileyhales.com) and [Chris Edwards](https://github.com/chris3edwards3/), 2019. Based on the [GLDAS Data Visualizer](https://github.com/rileyhales/gldas) and the [GFS Visualization Tool](https://github.com/rileyhales/gfs). Developed at the BYU Hydroinformatics Lab.

## Methodology
This application allows the user to view risks of flash floods in near-real-time using the Flash Flood Guidance System (FFGS) and a variety of forecast models which vary by region. Each region where the FFGS is established can use the GFS model's results in addition to other models that may be configured on a case-by-case basis. 

### The primary workflow of the app
1. Download the GFS/Forecast Model's most recent results for the Accumulated Precipitation variable (short name acpc in the grib file). GFS data are GRIB type.
1. Process the forecast data into a usable formats, namely GeoTiff files for geoprocessing and to netCDF files for time animated map generation.
1. Perform Geoprocessing on the GeoTiff files:
1. Resample the tif files to about 100x their resolution to facilitate geoprocessing relatively coarse forecasted raster data with very small watershed boundaries derived from the FFGS.
1. Perform zonal statistics on the resampled rasters within the boundaries of each of the FFGS watershed polygons. The statistics computed are the average precipitation value and the maximum precipitation value for the raster cells within the watershed polygons.
1. Compare the average and maximum value with the most recently generated FFGS threshold values.
1. Create a file containing these zonal statistics results which get used to style the map and chart in the user interface.
1. Generate a netCDF Markup Language file which will aggregate the netCDF files across their time steps and make the data viewable on the map and animate it vs time.
1. Delete the intermediate files generated.

### Accuracy limitations
The accuracy of this application is limited by:
1. The resolution and accuracy of the forecasting models being used
1. The accuracy of the thresholds for flood values determined by the FFGS models
1. The potential difference between FFGS and Precipitation Forecast time-intervals

### Possible error and disclaimers:
1. The charts and maps show only the values of precipitation accumulation from the forecast models. No attempt is made to account for losses to hydrologic factors such as evaporation, infiltration to groundwater, initial abstraction/storage, and so forth
1. No attempts are made to route the water to the drainage line or further down stream to determine the time of the flood. The charts indicate how long until enough water has accumulated to meet the threshold for precipitation given by the FFGS. They do not indicate that the flood will occur at the time the cumulative accumulation exceeds the threshold or determine if that is within the time constraints of the flash flood thresholds. The hydrologic losses, distribution of storm precipitation, and timing of flow will cause a difference between the chart's time and the actual event time, assuming the forecasted values occur. 

### How to add a new Region
1. In options.py add to the list of ffgs regions with a new tuple in the format ```('Proper name of region', 'shortname')```
2. Also add a new function called ```shortname_models``` that returns a list of tuples with each of the models that region uses in the format ```[('GFS', 'gfs'), ('Other Model Proper Name', 'shortname')]```
3. In the thredds directory, make a new, empty directory named the same as the shortname
4. In the app workspace, make a new, empty directory named the same as the shortname
5. Get a copy of the shapefile for the ffgs boundaries in the new region in the WGS 1984 Geographic Coordinate System. Put it in the app workspace folder you just made under a folder called shapefiles. rename the shapefile ffgs_shortname 
6. Create a csv in the app workspace folder called ffgs_thresholds.csv and fill it with the current information. see other files for example format
7. (Optional but recommended) Create a new geojson for that shapefile and put it in a new/existing js file. If you make a new one, add it to the list of imports in base.html
8. In leaflet.js, add an entry to the geojson_sorter JSON in the format ```{'shortname': name of the geojson you just made}```
9. In leaflet.js, add an entry to the zoomOpts JSON in the format ```{'shortname': [zoom level, [center_lat, center_lon]]}```

### How to add a new model
1. Create a script that follow sthe general format of the gfsworkflow.py that will download and perform the geoprocessing on that region. Refer to "The Primary Workflow of the App" section of this document.
2. Add return messages to the function as a status updater that will be returned to the user and then call that function in controllers.py with the rest of the models in the run_workflows function.

Your new function must:
* Follow the folder structure and naming conventions used by this app. Refer to the installation instructions for diagrams of the necessary folders.
* Use the python logging module to print logging.info messages about the progress of your application.
* Return some kind of status message, whether or not the workflow run was finished successfully.
* Be region specific.


## File Structure and Naming Convention References
The file structure used by THREDDS should look like the following:
~~~~
ffgs
--->hispaniola (You are responsible for creating this folder when you install the application)
	--->gfs (created for every region)
		---><directory named for timestamp of the forecast>
			--->wms.ncml (what the app calls to retrieve the time animated raster maps)
			--->gribs (Directory, automatically created and deleted)
			--->netcdfs (Directory, automatically created and deleted)
			--->processed
	--->wrfpr (example of another model, your new model's workflow creates and fills this folder)
		---><directory named for timestamp of the forecast>
			--->wms.ncml (what the app calls to retrieve the time animated raster maps)
			--->gribs (Directory, automatically created and deleted)
			--->netcdfs (Directory, automatically created and deleted)
			--->processed
--->centralamerica (You are responsible for creating this folder when you install the application)
	--->gfs (created for every region)
		---><directory named for timestamp of the forecast>
			--->wms.ncml (what the app calls to retrieve the time animated raster maps)
			--->gribs (Directory, automatically created and deleted)
			--->netcdfs (Directory, automatically created and deleted)
			--->processed
	etc...
~~~~

The App Workspace should look like the following:
~~~~
ffgs
--->hispaniola (You are responsible for creating this folder when you install the application)
	--->shapefiles (Directory, fill this with the ffgs polygons shapefile in the WGS1984 GCS)
		--->ffgs_hispaniola.shp
		--->ffgs_hispaniola.prj
		--->ffgs_hispaniola.dbf
		etc...
	--->ffgs_thresholds.csv (needs to be updated regularly with the most recent ffgs values
	--->gfsresults.csv (automatically created/updated in the workflow, contains average precipitation in each ffgs watershed)
	--->gfscolorscales.csv (automatically created/updated in the workflow, contains the values used to color the geojsons on the map)
	--->other csv results and colorscales files for other models
	
	--->GeoTIFFs (directory, automatically created/filled/deleted in the workflow)	
		--->time_of_forecast_step.tif for each forecast step downloaded
	--->GeoTIFFs_resampled (directory, automatically created/filled/deleted in the workflow)	
		--->time_of_forecast_step.tif resampled for correct geoprocessing
~~~~


## Installation Instructions
### 1 Install the Tethys App
This application is compatible with Tethys 2.X and Tethys 3 Distributions and is compatible with both Python 2 and 3 and Django 1 and 2. Install the latest version of Tethys before installing this app. This app requires the python packages: numpy, netcdf4, ogr, osr. Both should be installed automatically as part of this installation process.

Before installing this app on your Tethys portal, run the following install commands to install the dependencies.
~~~~
conda install netCDF4, datetime, xarray 
conda install -c conda-forge rasterstats
conda install -c conda-forge rasterio
~~~~
On the terminal of the server enter the tethys environment with the ```t``` command. ```cd``` to the directory where you install apps then run the following commands:  
~~~~
git clone https://github.com/rileyhales/ffgs.git  
cd ffgs
python setup.py develop
~~~~  
If you are on a production server, run:
~~~~
tethys manage collectstatic
~~~~
Reset the server, then attempt to log in through the web interface as an administrator. The app should appear in the Apps Library page in grey indicating you need to configure the custom settings.

The shapefile containing the FFGS watershed boundaries must be in a Geographic Coordinate System (GCS) such as WGS-1984.

### 2 Set up a Thredds Server (GFS Rasters)
Refer to the documentation for Thredds to set up an instance of Thredds on your tethys server.

In the public folder where your datasets are stored, create a new folder called ```ffgs```. Within the ffgs folder, create another folder named for each of the regions you want to see in the app. For example, it might look something like this: 
~~~~
ffgs
--->hispaniola
	---><empty directory>
--->centralamerica
	---><empty directory>
~~~~
The app will automatically create a file structure for each region and fill it with data. Refer to the "File Structure and Naming Convention Reference" for more information
#### Configure Thredds' settings (if you haven't previously)
You will also need to modify Thredds' settings files to enable WMS services and support for netCDF files on your server. In the folder where you installed Thredds, there should be a file called ```catalog.xml```. 
~~~~
vim catalog.xml
~~~~
Type ```a``` to begin editing the document.

At the top of the document is a list of supported services. Make sure the line for wms is not commented out.
~~~~
<service name="wms" serviceType="WMS" base="/thredds/wms/" />
~~~~
Scroll down toward the end of the section that says ```filter```. This is the section that limits which kinds of datasets Thredds will process. We need it to accept .nc, .nc4, and .ncml file types. Make sure your ```filter``` tag includes the following lines.
~~~~
<filter>
    <include wildcard="*.nc"/>
    <include wildcard="*.nc4"/>
    <include wildcard="*.ncml"/>
</filter>
~~~~
Press ```esc``` then type ```:x!```  and press the ```return``` key to save and quit.
~~~~
vim threddsConfig.xml
~~~~
Find the section near the top about CORS (Cross-Origin Resource Sharing). CORS allows Thredds to serve data to servers besides the host where it is located. Depending on your exact setup, you need to enable CORS by uncommenting these tags.
~~~~
<CORS>
    <enabled>true</enabled>
    <maxAge>1728000</maxAge>
    <allowedMethods>GET</allowedMethods>
    <allowedHeaders>Authorization</allowedHeaders>
    <allowedOrigin>*</allowedOrigin>
</CORS>
~~~~
Press ```esc``` then type ```:x!```  and press the ```return``` key to save and quit.

Reset the Thredds server so the catalog is regenerated with the edits that you've made. The command to reset your server will vary based on your installation method, such as ```docker reset thredds``` or ```sudo systemctl reset tomcat```.

### 3 Specify The Custom Settings
Log in to your Tethys portal as an admin. Click on the grey GLDAS box and specify these settings:

**Local File Path:** This is the full path to the directory named ffgs that you should have created within the thredds data directory during step 2. You can get this by navigating to that folder in the terminal and then using the ```pwd``` command. (example: ```/tomcat/content/thredds/ffgs/```)  

**Thredds Base Address:** This is the base URL to Thredds WMS services that the app uses to build urls for each of the WMS layers generated for the netcdf datasets. If you followed the typical configuration of thredds (these instructions) then your base url will look something like ```yourserver.com/thredds/wms/testAll/ffgs/```. You can verify this by opening the thredds catalog in a web browser (typically at ```yourserver.com/thredds/catalog.html```). Navigate to one of the FFGS netcdf files and click the WMS link. A page showing an xml document should load. Copy the url in the address bar until you get to the ```/ffgs/``` folder in that url. Do not include ```/hispaniola/processed/netcdf.nc``` or the request that comes after. (example: ```https://tethys.byu.edu/thredds/wms/testAll/ffgs/```)


## Data References

### Flash Flood Guidance System (FFGS)
* [http://www.wmo.int/ffgs](http://www.wmo.int/ffgs)
* [http://www.wmo.int/pages/prog/hwrp/flood/ffgs/documents/2017-ffgs-brochure-en.pdf](http://www.wmo.int/pages/prog/hwrp/flood/ffgs/documents/2017-ffgs-brochure-en.pdf)

### Global Forecast System (GFS)
Data Set: GFS 0.25 Degree
* [https://nomads.ncep.noaa.gov/](https://nomads.ncep.noaa.gov/)
* [https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs)

### Weather Research and Forecasting (WRF)
Description: AWIPS 3.8km Puerto Rico ARW (NCAR Advanced Research WRF)
* [https://www.nco.ncep.noaa.gov/pmb/products/hiresw/](https://www.nco.ncep.noaa.gov/pmb/products/hiresw/)
