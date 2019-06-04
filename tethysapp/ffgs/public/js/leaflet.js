////////////////////////////////////////////////////////////////////////  MAP FUNCTIONS
function map() {
    // create the map
    return L.map('map', {
        zoom: 8.25,
        minZoom: 1.25,
        boxZoom: true,
        maxBounds: L.latLngBounds(L.latLng(-100.0, -270.0), L.latLng(100.0, 270.0)),
        center: [18.8, -71],
        timeDimension: true,
        timeDimensionControl: true,
        timeDimensionControlOptions: {
            position: "bottomleft",
            autoPlay: true,
            loopButton: true,
            backwardButton: true,
            forwardButton: true,
            timeSliderDragUpdate: true,
            minSpeed: 1,
            maxSpeed: 6,
            speedStep: 1,
        },
    });
}

function basemaps() {
    // create the basemap layers
    let Esri_WorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}');
    let Esri_WorldTerrain = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}', {maxZoom: 13});
    let Esri_Imagery_Labels = L.esri.basemapLayer('ImageryLabels');
    return {
        "ESRI Imagery": L.layerGroup([Esri_WorldImagery, Esri_Imagery_Labels]).addTo(mapObj),
        "ESRI Terrain": L.layerGroup([Esri_WorldTerrain, Esri_Imagery_Labels])
    }
}

////////////////////////////////////////////////////////////////////////  WMS LAYERS FOR GLDAS
function newLayer() {
    let wmsurl = threddsbase + '/' + $("#region").val() + '/' + $("#model").val() + '/' + 'wms.ncml';
    let wmsLayer = L.tileLayer.wms(wmsurl, {
        // version: '1.3.0',
        layers: 'tp',
        dimension: 'time',
        useCache: true,
        crossOrigin: false,
        format: 'image/png',
        transparent: true,
        opacity: $("#opacity_raster").val(),
        BGCOLOR: '0x000000',
        styles: 'boxfill/' + $('#colorscheme').val(),
        colorscalerange: '0,50'
    });

    return L.timeDimension.layer.wms(wmsLayer, {
        name: 'time',
        requestTimefromCapabilities: true,
        updateTimeDimension: true,
        updateTimeDimensionMode: 'replace',
        cache: 20,
    }).addTo(mapObj);
}

////////////////////////////////////////////////////////////////////////  LEGEND DEFINITIONS
let forecastLegend = L.control({position: 'bottomright'});
forecastLegend.onAdd = function () {
    let div = L.DomUtil.create('div', 'legend');
    let url = threddsbase + '/' + $("#region").val() + '/' + $("#model").val() + '/' + 'wms.ncml' + "?REQUEST=GetLegendGraphic&LAYER=tp" + "&PALETTE=" + $('#colorscheme').val() + "&COLORSCALERANGE=0,50";
    div.innerHTML = '<img src="' + url + '" alt="legend" style="width:100%; float:right;">';
    return div
};

////////////////////////////////////////////////////////////////////////  GEOJSON LAYERS - GEOSERVER + WFS / GEOJSON
function layerPopups(feature, layer) {
    let watershed_id = feature.properties.cat_id;
    layer.bindPopup('<strong>Catchment ID: ' + watershed_id + '</strong>');
    layer.on('click', function () {
        id = watershed_id;
        updateChart(watershed_id);
    });
}

// create this reference array that other functions will build on
let watersheds;
let watersheds_colors;
let geojson_sorter = {
    'hispaniola': hispaniola_json,
    // 'centralamerica': centralamerica_json,
    // 'nepal', nepal_json,
    // regionname: regionname_json for each region that is configured
};

function colorScale(value) {
    return value > 30 ? '#0c2c84' :
        value > 25  ? '#225ea8' :
        value > 20  ? '#1d91c0' :
        value > 15  ? '#41b6c4' :
        value > 10   ? '#7fcdbb' :
        value > 5   ? '#c7e9b4' :
        value >= 0   ? '#ffffcc':
        ''
}

function setColor(rules, number) {
    return rules[number + '.0']['mean'] > 30 ? colorScale(30) :
        rules[number + '.0']['mean'] > 25 ? colorScale(25) :
        rules[number + '.0']['mean'] > 20 ? colorScale(20) :
        rules[number + '.0']['mean'] > 15 ? colorScale(15) :
        rules[number + '.0']['mean'] > 10 ? colorScale(10) :
        rules[number + '.0']['mean'] > 5 ? colorScale(5) :
        rules[number + '.0']['mean'] >= 0 ? colorScale(0) :
        '';
}


function addFFGSlayer() {
    let region = $("#region").val();
    // add the color-coordinated watersheds layer
    $.ajax({
        url: '/apps/ffgs/ajax/getColorScales/',
        async: false,
        data: JSON.stringify({region: region, model: $("#model").val()}),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (rules) {
            watersheds_colors = L.geoJSON(geojson_sorter[region], {
                onEachFeature: layerPopups,
                style: (function (feature) {
                    let number = feature.properties.cat_id;
                    return {
                        color: 'rgba(0,0,0,0.0)',
                        opacity: 0,
                        weight: 0,
                        fillColor: setColor(rules, number),
                        fillOpacity: $("#opacity_geojson").val()
                    }
                }),
            }).addTo(mapObj);
        }
    });

    // add the watershed boundaries layer
    watersheds = L.geoJSON(geojson_sorter[region], {
        onEachFeature: layerPopups,
        style: {
            color: '#000000',
            weight: 1,
            opacity: 1,
            fillColor: 'rgba(0,0,0,0.0)',
            fillOpacity: 0,
            // dashArray: '3',
        }
    }).addTo(mapObj);

    let ffgsLegend = L.control({position: 'bottomleft'});
	ffgsLegend.onAdd = function (mapObj) {
		let div = L.DomUtil.create('div', 'info legend'),
			grades = [0, 5, 10, 15, 20, 25, 30],
			labels = [];
		labels.push('<b>Precipitation (mm)</b>');
		for (let i = 0; i < grades.length; i++) {
			let from = grades[i];
			let to = grades[i + 1];
			labels.push('<i style="background:' + colorScale(from) + '"></i> ' + from + (to ? '&ndash;' + to : '+'));
		}
		div.innerHTML = labels.join('<br>');
		return div;
	};
	ffgsLegend.addTo(mapObj);
}

////////////////////////////////////////////////////////////////////////  MAP CONTROLS AND CLEARING
// the layers box on the top right of the map
function makeControls() {
    return L.control.layers(basemapObj, {
        'Forecast Layer': layerObj,
        'Colored Watersheds': watersheds_colors,
        'Watershed Boundaries': watersheds,
    }).addTo(mapObj);
}

// you need to remove layers when you make changes so duplicates dont persist and accumulate
function clearMap() {
    // remove the controls for the wms layer then remove it from the map
    controlsObj.removeLayer(layerObj);
    mapObj.removeLayer(layerObj);
    controlsObj.removeLayer(watersheds);
    mapObj.removeLayer(watersheds);
    controlsObj.removeLayer(watersheds_colors);
    mapObj.removeLayer(watersheds_colors);
    // now delete the controls object
    mapObj.removeControl(controlsObj);
}