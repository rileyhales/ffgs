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


////////////////////////////////////////////////////////////////////////  FUNCTIONS FOR GETTING VARIABLES
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

function get_regionmodel() {
    let region = $("#region").val();
    let model;
    if (region === 'hispaniola') {
        model = $("#hisp_models").val()
    } else if (region === 'centralamerica') {
        model = $("#central_models").val()
    }
    return [region, model]
}

////////////////////////////////////////////////////////////////////////  LOAD THE MAP
let threddsbase;
getThreddswms();                        // sets the value of threddsbase and geoserverbase
const mapObj = map();                   // used by legend and draw controls
const basemapObj = basemaps();          // used in the make controls function

////////////////////////////////////////////////////////////////////////  LAYER CONTROLS, MAP EVENTS, LEGEND
mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(4) + ', Lon: ' + event.latlng.lng.toFixed(4));
});

let forecastLayerObj = newForecastLayer();              // adds the wms raster layer
addFFGSlayer();                         // adds the ffgs watershed layer chosen by the user
let controlsObj = makeControls();       // the layer toggle controls top-right corner

forecastLegend.addTo(mapObj);           // add the legend for the WMS forecast layer
ffgsLegend.addTo(mapObj);               // add the legend for the colored geojson layer

////////////////////////////////////////////////////////////////////////  LISTENERS FOR CONTROLS ON THE MENU
function changemap() {
    clearMap();
    addFFGSlayer();
    forecastLayerObj = newForecastLayer();
    controlsObj = makeControls();
    forecastLegend.addTo(mapObj);
    updateChart(id);
}

$("#region").change(function () {
    let region = this.options[this.selectedIndex].value;
    if (region === 'hispaniola') {
        $("#hisp_models_wrapper").show();
        $("#hisp_dates_wrapper").show();
        $("#central_models_wrapper").hide();
        $("#central_dates_wrapper").hide();
    } else if (region === 'centralamerica') {
        $("#hisp_models_wrapper").hide();
        $("#hisp_dates_wrapper").hide();
        $("#central_models_wrapper").show();
        $("#central_dates_wrapper").show();
    }

    let opts = zoomOpts[$("#region").val()];
    clearMap();
    mapObj.setView(opts[1], opts[0]);
    addFFGSlayer();
    forecastLayerObj = newForecastLayer();
    controlsObj = makeControls();
    forecastLegend.addTo(mapObj);
    chart = placeholderChart();
});

$("#hisp_models").change(function () {
    changemap()
});

$("#central_models").change(function () {
    changemap()
});


$("#displaytoggle").click(function() {
    $("#displaycontrols").toggle();
});

$("#chartoptions").change(function () {
    updateChart(id);
});

$('#colorscheme').change(function () {
    changemap()
});

$("#opacity_raster").change(function () {
    forecastLayerObj.setOpacity($("#opacity_raster").val())
});
