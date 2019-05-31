// Global Highcharts options
Highcharts.setOptions({
    lang: {
        downloadCSV: "Download CSV",
        downloadJPEG: "Download JPEG image",
        downloadPDF: "Download PDF document",
        downloadPNG: "Download PNG image",
        downloadSVG: "Download SVG vector image",
        downloadXLS: "Download XLS",
        loading: "Timeseries loading, please wait...",
        noData: "No Data Selected. Place a point, draw a polygon, or select a region."
    },
});

let chartdata = null;

// todo the charts we want can be modified from the saldasforecast app and the malaria app. these wont help

// Placeholder chart
let chart = Highcharts.chart('highchart', {
    title: {
        align: "center",
        text: "Timeseries Data Chart Placeholder",
    },
    series: [{
        data: [],
    }],
    chart: {
        animation: true,
        zoomType: 'x',
        borderColor: '#000000',
        borderWidth: 2,
        type: 'area',
    },
    noData: {
        style: {
            fontWeight: 'bold',
            fontSize: '15px',
            color: '#303030'
        }
    },
});

function newHighchart(data) {
    chart = Highcharts.chart('highchart', {
        title: {
            align: "center",
            text: data['name'] + ' v Time ' + data['type'],
        },
        xAxis: {
            type: 'datetime',
            title: {text: "Time"},
        },
        yAxis: {
            title: {text: data['units']}
        },
        series: [{
            data: data['values'],
            type: "line",
            name: data['name'],
            tooltip: {
                xDateFormat: '%A, %b %e, %Y',
            },
        }],
        chart: {
            animation: true,
            zoomType: 'xy',
            borderColor: '#000000',
            borderWidth: 2,
            type: 'area',

        },

    });
}

function getDrawnChart(drawnItems) {
    // if there's nothing to get charts for then quit
    let geojson = drawnItems.toGeoJSON()['features'];
    if (geojson.length === 0 && currentregion === '') {
        return
    }

    // if there's geojson data, update that chart
    if (geojson.length > 0) {
        chart.hideNoData();
        chart.showLoading();

        //  Compatibility if user picks something out of normal bounds
        let coords = geojson[0]['geometry']['coordinates'];
        for (let i in coords.length) {
            if (coords[i] < -180) {
                coords[i] += 360;
            }
            if (coords[i] > 180) {
                coords[i] -= 360;
            }
        }

        // setup a parameters json to generate the right timeseries
        let data = {
            coords: coords,
            geojson: geojson[0],
            variable: $('#variables').val(),
            time: $("#dates").val(),
        };

        // decide which ajax url you need based on drawing type
        let url;
        let drawtype = geojson[0]['geometry']['type'];
        if (drawtype === 'Point') {
            url = '/apps/gldas/ajax/getPointSeries/';
        } else {
            url = '/apps/gldas/ajax/getPolygonAverage/';
        }

        $.ajax({
            url: url,
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: "application/json",
            method: 'POST',
            success: function (result) {
                chartdata = result;
                makechart();
            }
        })
        // If there isn't any geojson, then you actually should refresh the shapefile chart (ie the data is the lastregion)
    } else {
        getShapeChart('lastregion');
    }
}
