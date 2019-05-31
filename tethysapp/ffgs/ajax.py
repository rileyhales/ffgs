import ast
import pandas
import calendar
import datetime

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
    data = ast.literal_eval(request.body.decode('utf-8'))
    id = data['watershedID']
    wrksppath = app_settings()['app_wksp_path']

    results = os.path.join(wrksppath, 'zonal_stats_2019053100_00.csv')
    df = pandas.read_csv(results)[['cat_id', 'mean', 'Timestep']]
    df = df.query("cat_id == @id")

    values = []
    for row in df.iterrows():
        time = datetime.datetime.strptime(row[1]['Timestep'], "%m/%d/%Y")
        time = calendar.timegm(time.utctimetuple()) * 1000
        values.append([time, row[1]['mean']])

    threshold_table = os.path.join(wrksppath, data['region'], 'ffgs_thresholds.csv')
    df = pandas.read_csv(threshold_table)[['BASIN', '01FFG2018021312']]
    df = df.query("BASIN == @id")
    threshold = df['01FFG2018021312'].values[0]

    maximum = max(values)[1]
    if threshold > maximum:
        maximum = threshold

    return JsonResponse({'values': values, 'threshhold': threshold, 'max': maximum})
