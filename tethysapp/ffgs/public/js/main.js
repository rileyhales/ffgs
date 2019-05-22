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


// ////////////////////////////////////////////////////////////////////////  AJAX FUNCTIONS
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

// ////////////////////////////////////////////////////////////////////////  LOAD THE MAP
let threddsbase;
getThreddswms();                        // sets the value of threddsbase and geoserverbase
const mapObj = map();                   // used by legend and draw controls
const basemapObj = basemaps();          // used in the make controls function
