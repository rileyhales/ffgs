////////////////////////////////////////////////////////////////////////  MAP FUNCTIONS
const zoomOpts = {
    // 'region name': [zoom, [lat_center, lon_center]]
    'hispaniola': [8.25, [18.8, -71]],
    'centralamerica': [5, [12.5, -86]]
};

function map() {
    // create the map
    let opts = zoomOpts[$("#region").val()];
    return L.map('map', {
        zoom: opts[0],
        minZoom: 1.25,
        boxZoom: true,
        maxBounds: L.latLngBounds(L.latLng(-100.0, -270.0), L.latLng(100.0, 270.0)),
        center: opts[1],
        timeDimension: true,
        timeDimensionControl: true,
        timeDimensionControlOptions: {
            position: "bottomleft",
            autoPlay: true,
            loopButton: true,
            backwardButton: true,
            forwardButton: true,
            timeSliderDragUpdate: true,
            minSpeed: 2,
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
        "ESRI Imagery with Labels": L.layerGroup([Esri_WorldImagery, Esri_Imagery_Labels]).addTo(mapObj),
        "ESRI Imagery": L.layerGroup([Esri_WorldImagery]),
        "ESRI Terrain": L.layerGroup([Esri_WorldTerrain, Esri_Imagery_Labels])
    }
}

////////////////////////////////////////////////////////////////////////  WMS LAYERS FOR GLDAS
function newForecastLayer() {
    let regionmodel = get_regionmodel();
    let region = regionmodel[0];
    let model = regionmodel[1];
    let wmsurl = threddsbase + '/' + region + '/' + model + '/' + 'wms.ncml';
    let max = String(parseInt($("#legendintervals").val()) * 6);
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
        colorscalerange: '0,' + max
    });

    return L.timeDimension.layer.wms(wmsLayer, {
        name: 'time',
        requestTimefromCapabilities: true,
        updateTimeDimension: true,
        updateTimeDimensionMode: 'replace',
        cache: 20,
    }).addTo(mapObj);
}
////////////////////////////////////////////////////////////////////////  FORECAST LAYER LEGEND
// the forecast layer raster legend
let forecastLegend = L.control({position: 'topright'});
forecastLegend.onAdd = function () {
    let regionmodel = get_regionmodel();
    let region = regionmodel[0];
    let model = regionmodel[1];
    let max = String(parseInt($("#legendintervals").val()) * 6);
    let div = L.DomUtil.create('div', 'legend');
    let url = threddsbase + '/' + region + '/' + model + '/' + 'wms.ncml' + "?REQUEST=GetLegendGraphic&LAYER=tp" + "&PALETTE=" + $('#colorscheme').val() + "&COLORSCALERANGE=0," + max;
    div.innerHTML = '<img src="' + url + '" alt="legend" style="width:100%; float:right;">';
    return div
};

// the geojson (colored watersheds) legend
let ffgsLegend = L.control({position: 'bottomleft'});
ffgsLegend.onAdd = function () {
    let div = L.DomUtil.create('div', 'info legend');
    let interval = parseInt($("#legendintervals").val());
    let labels = [];

    labels.push('<b>Precipitation (mm)</b>');
    for (let i = 0; i < 6; i++) {
        let from = interval * i;
        let to = interval * (i + 1);
        labels.push('<i style="background:' + colorScale(from) + '"></i> ' + from + '&ndash;' + to);
    }
    labels.push('<i style="background:' + colorScale((interval * 6)) + '"></i> ' + ((interval * 6)) + '+');
    div.innerHTML = labels.join('<br>');
    return div;
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
    // regionname: regionname_json for each region that is configured
    'hispaniola': hispaniola_json,
    'centralamerica': centralamerica_json,
    // 'nepal', nepal_json,
};

function colorScale(value) {
    let interval = parseInt($("#legendintervals").val());
    return value >= (interval * 6) ? '#0c2c84' :
    value >= (interval * 5)  ? '#225ea8' :
    value >= (interval * 4)  ? '#1d91c0' :
    value >= (interval * 3)  ? '#41b6c4' :
    value >= (interval * 2)   ? '#7fcdbb' :
    value >= interval  ? '#c7e9b4' :
    value >= 0   ? '#ffffcc':
    ''
}

let rules;
function setColor(rules, number, resulttype) {
    let interval = parseInt($("#legendintervals").val());
    return rules[number + '.0'][resulttype] >= (interval * 6) ? colorScale(30) :
        rules[number + '.0'][resulttype] >= (interval * 5) ? colorScale(25) :
        rules[number + '.0'][resulttype] >= (interval * 4) ? colorScale(20) :
        rules[number + '.0'][resulttype] >= (interval * 3) ? colorScale(15) :
        rules[number + '.0'][resulttype] >= (interval * 2) ? colorScale(10) :
        rules[number + '.0'][resulttype] >= interval ? colorScale(5) :
        rules[number + '.0'][resulttype] >= 0 ? colorScale(0) :
        '';
}

function addFFGSlayer() {
    let regionmodel = get_regionmodel();
    let region = regionmodel[0];
    let model = regionmodel[1];
    // add the color-coordinated watersheds layer
    $.ajax({
        url: '/apps/ffgs/ajax/getColorScales/',
        async: false,
        data: JSON.stringify({region: region, model: model}),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (data) {
            rules = data;
            watersheds_colors = L.geoJSON(geojson_sorter[region], {
                onEachFeature: layerPopups,
                style: (function (feature) {
                    let number = feature.properties.cat_id;
                    return {
                        color: 'rgba(0,0,0,0.0)',
                        opacity: 0,
                        weight: 0,
                        fillColor: setColor(rules, number, $("#resulttype").val()),
                        fillOpacity: 1,
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
        'Forecast Layer': forecastLayerObj,
        'Colored Watersheds': watersheds_colors,
        'Watershed Boundaries': watersheds,
    }).addTo(mapObj);
}

// you need to remove layers when you make changes so duplicates dont persist and accumulate
function clearMap() {
    // remove the controls for the wms layer then remove it from the map
    controlsObj.removeLayer(forecastLayerObj);
    mapObj.removeLayer(forecastLayerObj);
    controlsObj.removeLayer(watersheds);
    mapObj.removeLayer(watersheds);
    controlsObj.removeLayer(watersheds_colors);
    mapObj.removeLayer(watersheds_colors);
    // now delete the controls object
    mapObj.removeControl(controlsObj);
}