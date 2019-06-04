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
        success: function (result) {
            watersheds_colors = L.geoJSON(geojson_sorter[region], {
                onEachFeature: layerPopups,
                style: (function (feature) {
                    let id = feature.properties.cat_id;
                    let opacity = $("#opacity_geojson").val();
                    switch (true) {
                        case result[id + '.0']['mean'] >= 30:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: '#0012ff', fillOpacity: opacity};
                        case result[id + '.0']['mean'] >= 25:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: '#00deff', fillOpacity: opacity};
                        case result[id + '.0']['mean'] >= 20:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: '#00ff00', fillOpacity: opacity};
                        case result[id + '.0']['mean'] >= 15:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: '#fffc00', fillOpacity: opacity};
                        case result[id + '.0']['mean'] >= 10:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: '#ff7700', fillOpacity: opacity};
                        case result[id + '.0']['mean'] >= 5:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: '#ff000f', fillOpacity: opacity};
                        case result[id + '.0']['mean'] < 5:
                            return {color: 'rgba(0,0,0,0.0)', opacity: 0, weight: 0, fillColor: 'rgba(119,120,124,0.53)', fillOpacity: opacity};
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