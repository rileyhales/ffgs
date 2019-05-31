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

function newHighchart() {
    chart = Highcharts.chart('highchart', {
        title: {
            align: "center",
            text: 'Forecasted Precipitation Accumulation v Time ',
        },
        xAxis: {
            title: {text: "Time"},
            type: 'datetime',
        },
        yAxis: {
            title: {text: 'millimeters'},   // should be millimeters
            max: chartdata['max'],
            plotLines: [{
                value: chartdata['threshhold'],
                color: 'red',
                dashStyle: 'shortdash',
                width: 3,
                label: {
                    text: 'Flash Flood Threshold Depth - ' + String(chartdata['max'])
                }
            }],
        },
        series: [{
            data: chartdata['values'],          // the series of data
            type: 'column',
            name: 'Accumulated Precipitation per Day',            // the name of the series
            tooltip: {
                xDateFormat: '%A, %b %e, %Y',
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

    $.ajax({
        url: '/apps/ffgs/ajax/getFloodChart/',
        data: JSON.stringify({region: $("#region").val(), watershedID: ID}),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            chartdata = result;
            newHighchart();
        }
    })
}
