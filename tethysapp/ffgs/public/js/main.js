// Getting the csrf token
let csrftoken = Cookies.get('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


////////////////////////////////////////////////////////////////////////  AJAX FUNCTIONS
function getThreddswms() {
    $.ajax({
        url: '/apps/ffgs/ajax/getCustomSettings/',
        async: false,
        data: '',
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            threddsbase = result['threddsurl'];
        },
    });
}

////////////////////////////////////////////////////////////////////////  LOAD THE MAP
let threddsbase;
getThreddswms();                        // sets the value of threddsbase and geoserverbase
const mapObj = map();                   // used by legend and draw controls
const basemapObj = basemaps();          // used in the make controls function

////////////////////////////////////////////////////////////////////////  LAYER CONTROLS, MAP EVENTS, LEGEND
mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(5) + ', Lon: ' + event.latlng.lng.toFixed(5));
});

let layerObj = newLayer();              // adds the wms raster layer
addFFGSlayer();                         // adds the ffgs watershed layer chosen by the user
let controlsObj = makeControls();       // the layer toggle controls top-right corner
legend.addTo(mapObj);                   // add the legend graphic to the map

////////////////////////////////////////////////////////////////////////  EVENT LISTENERS
$("#opacity_raster").change(function () {
    layerObj.setOpacity($('#opacity_raster').val());
});

$('#colorscheme').change(function () {
    clearMap();
    addFFGSlayer();
    layerObj = newLayer();
    controlsObj = makeControls();
    legend.addTo(mapObj);
});

$("#opacity_geojson").change(function () {
    watersheds.setStyle({opacity: $("#opacity_geojson").val()});
});

$("#datatoggle").click(function() {
    $("#datacontrols").toggle();
});

$("#displaytoggle").click(function() {
    $("#displaycontrols").toggle();
});

$("#chartoptions").change(function () {
    updateChart(id);
});