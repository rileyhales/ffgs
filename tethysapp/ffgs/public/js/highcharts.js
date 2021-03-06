// Global Highcharts options
Highcharts.setOptions({
    lang: {
        downloadCSV: "Download CSV",
        downloadJPEG: "Download JPEG image",
        downloadPDF: "Download PDF document",
        downloadPNG: "Download PNG image",
        downloadSVG: "Download SVG vector image",
        downloadXLS: "Download XLS",
        loading: "Searching forecast results for this watershed. Please wait...",
        noData: "No Data Selected. Click on a watershed to see forecast data."
    },
});

let chartdata = null;
let id = null;

// Placeholder chart
function placeholderChart() {
    return Highcharts.chart('highchart', {
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
}
let chart = placeholderChart();

function newHighchart() {
    chart = Highcharts.chart('highchart', {
        title: {
            align: "center",
            text: 'Forecasted Precipitation Accumulation vs. Time ',
        },
        subtitle: {
            align: "center",
            text: 'Catchment ID: ' + id,
        },
        xAxis: {
            title: {text: "Time (in UTC +0:00)"},
            type: 'datetime',
            units: [['hour', [6, 12, 18]], ['day', [1]]],
        },
        yAxis: {
            title: {text: 'millimeters'},   // should be millimeters
            max: chartdata['max'],
            plotLines: [{
                value: chartdata['threshold'],
                color: 'red',
                dashStyle: 'shortdash',
                width: 2,
                label: {
                    text: 'Flash Flood Threshold Depth: ' + String(chartdata['threshold'])
                },
                zIndex: 4,
            }],
        },
        series: [{
            data: chartdata['values'],          // the series of data
            type: 'column',
            name: 'Incremental Precipitation Accumulation',            // the name of the series
            tooltip: {
                xDateFormat: '%a, %b %e, %Y %H:%M'
            },
        }],
        chart: {
            animation: true,
            zoomType: 'xy',
            borderColor: '#000000',
            borderWidth: 2,
        },

    });
}


function newCumHighchart() {
    chart = Highcharts.chart('highchart', {
        title: {
            align: "center",
            text: 'Forecasted Precipitation (Cumulative) vs. Time ',
        },
        subtitle: {
            align: "center",
            text: 'Catchment ID: ' + id,
        },
        xAxis: {
            title: {text: "Time (in UTC +0:00)"},
            type: 'datetime',
            units: [['hour', [6, 12, 18]], ['day', [1]]],
        },
        yAxis: {
            title: {text: 'millimeters'},   // should be millimeters
            max: chartdata['max'],
            plotLines: [{
                value: chartdata['threshold'],
                color: 'red',
                dashStyle: 'shortdash',
                width: 2,
                label: {
                    text: 'Flash Flood Threshold Depth: ' + String(chartdata['threshold'])
                },
                zIndex: 4,
            }],
        },
        series: [{
            data: chartdata['values'],          // the series of data
            type: 'column',
            name: 'Cumulative Precipitation',            // the name of the series
            tooltip: {
                xDateFormat: '%a, %b %e, %Y %H:%M'
            },
        }],
        chart: {
            animation: true,
            zoomType: 'xy',
            borderColor: '#000000',
            borderWidth: 2,
        },

    });
}


function getFloodChart(ID) {
    chart.hideNoData();
    chart.showLoading();

    let regionmodel = get_regionmodel();
    let region = regionmodel[0];
    let model = regionmodel[1];

    $.ajax({
        url: '/apps/ffgs/ajax/getFloodChart/',
        data: JSON.stringify({region: region, model: model, watershedID: ID}),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            chartdata = result;
            newHighchart();
        }
    })
}

function getCumFloodChart(ID) {
    chart.hideNoData();
    chart.showLoading();

    let regionmodel = get_regionmodel();
    let region = regionmodel[0];
    let model = regionmodel[1];

    $.ajax({
        url: '/apps/ffgs/ajax/getCumFloodChart/',
        data: JSON.stringify({region: region, model: model, watershedID: ID}),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            chartdata = result;
            newCumHighchart();
        }
    })
}

function updateChart(ID) {
    let type = $("#chartoptions").val();
    if (ID !== null) {
        if (type === 'intervals') {
            getFloodChart(ID);
        }
        if (type === 'cumulative') {
            getCumFloodChart(ID);
        }
    }
}