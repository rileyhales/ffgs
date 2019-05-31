# Flash Flood Guidance System Risk Analyzer
This is a Tethys 2/3 compatible app that helps determine risk of flooding based on the Flash Flood Guidance System using the GFS and WRF forecasts as inputs for precipitation depths.

© [Riley Hales](http://rileyhales.com) and [Chris Edwards](https://github.com/chris3edwards3/), 2019. Based on the [GLDAS Data Visualizer](https://github.com/rileyhales/gldas) and the [GFS Visualization Tool](https://github.com/rileyhales/gfs). Developed at the BYU Hydroinformatics Lab.

Before installing this app on your Tethys portal, run the following install commands to install the dependencies.
~~~~
conda install netCDF4, datetime, xarray 
conda install -c conda-forge rasterstats
conda install -c conda-forge rasterio
~~~~
The shapefile containing the FFGS watershed boundaries must be in a Geographic Coordinate System (GCS) such as WGS-1984.

## Installation Instructions
### 1 Install the Tethys App
This application is compatible with Tethys 2.X and Tethys 3 Distributions and is compatible with both Python 2 and 3 and Django 1 and 2. Install the latest version of Tethys before installing this app. This app requires the python packages: numpy, netcdf4, ogr, osr. Both should be installed automatically as part of this installation process.

On the terminal of the server enter the tethys environment with the ```t``` command. ```cd``` to the directory where you install apps then run the following commands:  
~~~~
git clone https://github.com/rileyhales/gldas.git  
cd gldas
python setup.py develop
~~~~  
If you are on a production server, run:
~~~~
tethys manage collectstatic
~~~~
Reset the server, then attempt to log in through the web interface as an administrator. The app should appear in the Apps Library page in grey indicating you need to configure the custom settings.

### 2 Set up a Thredds Server (GLDAS Rasters)
Refer to the documentation for Thredds to set up an instance of Thredds on your tethys server.

In the public folder where your datasets are stored, create a new folder called ```ffgs```. Within the ffgs folder, create another folder named for each of the regions you want to see in the app. 
~~~~
ffgs
--->hispaniola
	--->gfs
		---><folder named for timestamp>
			--->gribs
			--->netcdfs
			--->processed
	--->wrf
		---><folder named for timestamp>
			--->gribs
			--->netcdfs
			--->processed
--->centralamerica
	--->gfs
		---><folder named for timestamp>
			--->gribs
			--->netcdfs
			--->processed
	--->other model types?
		---><folder named for timestamp>
			--->gribs
			--->netcdfs
			--->processed
~~~~

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

### 3 Set The Custom Settings
Log in to your Tethys portal as an admin. Click on the grey GLDAS box and specify these settings:

**Local File Path:** This is the full path to the directory named ffgs that you should have created within the thredds data directory during step 2. You can get this by navigating to that folder in the terminal and then using the ```pwd``` command. (example: ```/tomcat/content/thredds/ffgs/```)  

**Thredds Base Address:** This is the base URL to Thredds WMS services that the app uses to build urls for each of the WMS layers generated for the netcdf datasets. If you followed the typical configuration of thredds (these instructions) then your base url will look something like ```yourserver.com/thredds/wms/testAll/ffgs/```. You can verify this by opening the thredds catalog in a web browser (typically at ```yourserver.com/thredds/catalog.html```). Navigate to one of the FFGS netcdf files and click the WMS link. A page showing an xml document should load. Copy the url in the address bar until you get to the ```/ffgs/``` folder in that url. Do not include ```/hispaniola/processed/netcdf.nc``` or the request that comes after. (example: ```https://tethys.byu.edu/thredds/wms/testAll/ffgs/```)

## How to add a new Region
1. In options.py add to the list of ffgs regions with a new tuple in the format ('Proper name of region', 'shortname')
2. Add a folder in the thredds directory named the same as the shortname
3. Add a folder to the app workspace named the same as the shortname
4. Get a copy of the shapefile for the ffgs boundaries in the new region. Put it in the app workspace folder you just made under a folder called shapefiles. rename the shapefile ffgs_shortname 
5. Create a new geojson for that shapefile and put it in a new/existing js file. if you make a new one, add it to the list of imports in base.html
6. create a csv in the app workspace folder called ffgs_thresholds.csv and fill it with the current information. see other files for example format
6. In leaflet.js, add an entry to the dictionary in the format {'shortname': name of the geojson you just made}
7. Add the zoom and center information to the leaflet.js json object following the shortname, center, zoom patten

## How to add a new model
1. create a script to download all the timesteps of the forecast model and call it data_modelname.py
2. make it compatible with the ffgs workflow
