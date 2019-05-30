# Flash Flood Guidance System Risk Analyzer
This is a Tethys 2/3 compatible app that helps determine risk of flooding based on the Flash Flood Guidance System using the GFS and WRF forecasts as inputs for precipitation depths.

© [Riley Hales](http://rileyhales.com) and [Chris Edwards](https://github.com/chris3edwards3/), 2019. Based on the [GLDAS Data Visualizer](https://github.com/rileyhales/gldas) and the [GFS Visualization Tool](https://github.com/rileyhales/gfs). Developed at the BYU Hydroinformatics Lab.

Before installing this app on your Tethys portal, run the following install commands to install the dependencies.
~~~~
conda install netCDF4
conda install datetime
conda install -c conda-forge rasterstats
conda install -c conda-forge rasterio
~~~~
The shapefile containing the FFGS watershed boundaries must be in a Geographic Coordinate System (GCS) such as WGS-1984.

## Installing the App

Thredds needs to have the following file structure:
~~~~
ffgs
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
~~~~

