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

    // let layerObj = newLayer();              // adds the wms raster layer
addFFGSlayer();                         // adds the ffgs watershed layer chosen by the user
let controlsObj = makeControls();       // the layer toggle controls top-right corner

let ffgsLegend = L.control({position: 'bottomleft'});
ffgsLegend.onAdd = function () {
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

////////////////////////////////////////////////////////////////////////  EVENT LISTENERS
$('#colorscheme').change(function () {
    clearMap();
    addFFGSlayer();
    // layerObj = newLayer();
    controlsObj = makeControls();
        // forecastLegend.addTo(mapObj);
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

$("#region").change(function () {
    let opts = zoomOpts[$("#region").val()];
    clearMap();
    mapObj.setView(opts[1], opts[0]);
    // mapObj.panTo();
    addFFGSlayer();
    // layerObj = newLayer();
    controlsObj = makeControls();
});