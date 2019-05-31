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

    let timedLayer = L.timeDimension.layer.wms(wmsLayer, {
        name: 'time',
        requestTimefromCapabilities: true,
        updateTimeDimension: true,
        updateTimeDimensionMode: 'replace',
        cache: 20,
    }).addTo(mapObj);

    return timedLayer
}

////////////////////////////////////////////////////////////////////////  LEGEND DEFINITIONS
let legend = L.control({position: 'topright'});
legend.onAdd = function () {
    let div = L.DomUtil.create('div', 'legend');
    let url = threddsbase + '/' + $("#region").val() + '/' + $("#model").val() + '/' + 'wms.ncml' + "?REQUEST=GetLegendGraphic&LAYER=tp" + "&PALETTE=" + $('#colorscheme').val() + "&COLORSCALERANGE=0,50";
    div.innerHTML = '<img src="' + url + '" alt="legend" style="width:100%; float:right;">';
    return div
};

////////////////////////////////////////////////////////////////////////  GEOJSON LAYERS - GEOSERVER + WFS / GEOJSON
function layerPopups(feature, layer) {
    let watershed_id = feature.properties.cat_id;
    layer.bindPopup('<strong>This is watershed # ' + watershed_id + '</strong>');
    layer.on('click', function() {getFloodChart(watershed_id)});
}

// create this reference array that other functions will build on
let ffgs_watersheds;
let geojson_sorter = {
    'hispaniola': hispaniola_json,
    // 'centralamerica': centralamerica_json,
    // regionname: regionname_json for each region that is configured
};

function addFFGSlayer() {
    ffgs_watersheds = L.geoJSON(geojson_sorter[$("#region").val()], {
        onEachFeature: layerPopups,
        style: (function (feature) {
            switch (true) {
                case feature.properties.cat_id >= 2004701000:
                    return {color: '#00ff00', opacity: $("#opacity_geojson").val()};
                case feature.properties.cat_id < 2004701000:
                    return {color: '#ff00fd', opacity: $("#opacity_geojson").val()};
            }
        }),
    }).addTo(mapObj);
}

////////////////////////////////////////////////////////////////////////  MAP CONTROLS AND CLEARING
// the layers box on the top right of the map
function makeControls() {
    return L.control.layers(basemapObj, {
        'Forecast Layer': layerObj,
        'FFGS Watersheds': ffgs_watersheds,
    }).addTo(mapObj);
}

// you need to remove layers when you make changes so duplicates dont persist and accumulate
function clearMap() {
    // remove the controls for the wms layer then remove it from the map
    controlsObj.removeLayer(layerObj);
    mapObj.removeLayer(layerObj);
    controlsObj.removeLayer(ffgs_watersheds);
    mapObj.removeLayer(ffgs_watersheds);
    // now delete the controls object
    mapObj.removeControl(controlsObj);
}