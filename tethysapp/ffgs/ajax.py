import ast
import calendar

import pandas
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .options import *


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_settings (options)
    """
    return JsonResponse(app_settings())


@login_required()
def get_floodchart(request):
    """
    creates the bar chart for the watershedID in the request by reading the csv files of data
    Dependencies: app_settings (options), ast, pandas, calendar
    """
    # read the values sent from the javascript request
    data = ast.literal_eval(request.body.decode('utf-8'))
    id = data['watershedID']
    model = data['model']
    region = data['region']
    wrksppath = app_settings()['app_wksp_path']

    # read the csv of results from the last workflow run
    results = os.path.join(wrksppath, region, model + 'results.csv')
    df = pandas.read_csv(results)[['cat_id', 'mean', 'max', 'Timestep']]
    df = df.query("cat_id == @id")

    # get the timeseries values from the dataframe
    values = []
    for row in df.iterrows():
        time = datetime.datetime.strptime(str(int(row[1]['Timestep'])), "%Y%m%d%H")
        time = calendar.timegm(time.utctimetuple()) * 1000
        values.append([time, round(float(row[1]['mean']), 1)])

    # extract the threshold value from it's csv file
    threshold_table = os.path.join(wrksppath, region, 'ffgs_thresholds.csv')
    df = pandas.read_csv(threshold_table)[['BASIN', '01FFG2018021312']]
    df = df.query("BASIN == @id")
    threshold = round(float(df['01FFG2018021312'].values[0]), 1)

    # determine the max value the chart should be zoomed to
    maximum = max(values)[1]
    if threshold > maximum:
        maximum = threshold

    return JsonResponse({'values': values, 'threshold': threshold, 'max': maximum})


@login_required()
def get_cum_floodchart(request):
    """
    creates the bar chart for the watershedID in the request by reading the csv files of data
    Dependencies: app_settings (options), ast, pandas, calendar
    """
    # read the values sent from the javascript request
    data = ast.literal_eval(request.body.decode('utf-8'))
    id = data['watershedID']
    model = data['model']
    region = data['region']
    wrksppath = app_settings()['app_wksp_path']

    # read the csv of results from the last workflow run
    results = os.path.join(wrksppath, region, model + 'results.csv')
    df = pandas.read_csv(results)[['cat_id', 'mean', 'max', 'Timestep']]
    df = df.query("cat_id == @id")

    # get the timeseries values from the dataframe
    values = []
    cum_values = 0
    for row in df.iterrows():
        time = datetime.datetime.strptime(str(int(row[1]['Timestep'])), "%Y%m%d%H")
        time = calendar.timegm(time.utctimetuple()) * 1000
        cum_values = round(float(cum_values + row[1]['mean']), 1)
        values.append([time, cum_values])

    # extract the threshold value from it's csv file
    threshold_table = os.path.join(wrksppath, region, 'ffgs_thresholds.csv')
    df = pandas.read_csv(threshold_table)[['BASIN', '01FFG2018021312']]
    df = df.query("BASIN == @id")
    threshold = round(float(df['01FFG2018021312'].values[0]), 1)

    # determine the max value the chart should be zoomed to
    maximum = max(values)[1]
    if threshold > maximum:
        maximum = threshold

    return JsonResponse({'values': values, 'threshold': threshold, 'max': maximum})


@login_required()
def get_colorscales(request):
    """
    creates the bar chart for the watershedID in the request by reading the csv files of data
    Dependencies: app_settings (options), ast, pandas, calendar
    """
    # setup the function environment
    data = ast.literal_eval(request.body.decode('utf-8'))
    model = data['model']
    region = data['region']
    wrksppath = app_settings()['app_wksp_path']

    # read the color scale csv
    csv = os.path.join(wrksppath, region, model + 'colorscales.csv')
    df = pandas.read_csv(csv, usecols=['cat_id', 'cum_mean', 'mean', 'max'], index_col=0)

    return JsonResponse(df.to_dict(orient='index'))
